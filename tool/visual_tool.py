import json

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import altair as alt
from wordcloud import WordCloud


class VisualTool:
    # 한국어/영어 분포 시각화
    @staticmethod
    def plot_language_dist(language_distribution):
        base = alt.Chart(language_distribution).encode(
            theta = alt.Theta("count:Q", stack=True),
            radius = alt.Radius("count", scale = alt.Scale(type='sqrt', zero = True, rangeMin=20)),
            color = alt.Color('label:N', scale = alt.Scale(domain=['korean', 'english'], range=['#207a8f', '#b9d5db']), legend=None)
        )
        c1 = base.mark_arc(innerRadius=30, stroke='#0000')
        c2 = base.mark_text(radiusOffset=20).encode(text = 'label')

        chart = c1 + c2
        st.altair_chart(chart, theme = 'streamlit', use_container_width=True)

    # 선택한 카테고리 하이라이트
    @staticmethod
    def plot_cat_dist(category_distribution, search_queries, language):
        
        if not search_queries:
            colors = ['#207a8f'] * len(category_distribution)
        else:
            colors = [
                '#ff0000' if any(query.lower() == idx.lower() for query in search_queries) else '#207a8f'
                for idx in category_distribution['label']
            ]

        fig = px.bar(
            category_distribution,
            x = 'count',
            y = 'label',
            text = (category_distribution['count']/category_distribution['count'].sum()*100).round(2).astype(str) + '%',
            width = 800,
            height = 600,
            orientation = 'h',
            title = f"{language} 분포"
        ).update_yaxes(categoryorder = 'total ascending')
        fig.update_traces(marker_color = colors)
        st.plotly_chart(fig)
    
    # 초기에는 전체 오픈데이터 셋에서 일부 카테고리만 선택해서 띄우기 위해 사용했는데,
    # 최종적으로는 그럴 필요는 없어져서, 결국 한국어에 해당하는 카테고리 분포/ 영어에 해당하는 카테고리 분포를 따로 보기 위해 사용
    @staticmethod
    def plot_cat_partial(category_distribution, categories):
        # 선택된 카테고리들만 필터링
        temp_df = category_distribution.loc[category_distribution['label'].isin(categories)]

        # 퍼센트 계산
        temp_df['percentage'] = (temp_df['count'] / (temp_df['count'].sum())) * 100

        # 3% 미만 카테고리 그룹화
        major_df = temp_df[temp_df['percentage'] >= 3]
        minor_df = temp_df[temp_df['percentage'] < 3]

        # 기타 퍼센트 계산
        others_percent = minor_df['percentage'].sum()

        # 기타 정보 추가
        others_row = pd.DataFrame({'label': ['others'], 'percentage': [others_percent]})
        major_df = pd.concat([major_df, others_row], ignore_index = True)

        # 파이차트 생성
        fig = px.pie(
            major_df,
            names='label',      # 파이차트의 각 부분의 이름
            values='percentage', # 각 부분의 값
            width=450,
            height=400,
            category_orders={'label':major_df['label'].tolist()}
        )
        fig.update_layout(
            showlegend=False
        )
        # 차트 출력
        st.plotly_chart(fig)

        # 기타 상세 정보
        minor_df = minor_df.drop(columns=['count'])

        st.markdown(
            """
            <style>
            .st-emotion-cache-1h9usn1 {
                width: 130%;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # 기타(3퍼 미만)에 해당하는 카테고리에 대해 구체화하는 DF
        with st.expander('Others detail'):
            # st.dataframe 으로 expander 내에 넣으려 했는데, 가로 부분이 한번에 안들어가서 markdown 사용
            st.markdown(minor_df.style.hide(axis = 'index').to_html(), unsafe_allow_html=True)

    # 카테고리 내 하위카테고리의 분포 시각화(파이차트 OR 지도)
    @staticmethod
    def plot_subcategory_dist(subcategory_distribution, category = None):
        if category == None:
            labels = subcategory_distribution['label']
            values = subcategory_distribution['count']
            
            colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880']
            
            # 파이 차트 생성
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.4,  # 도넛 차트 모양(내부 빈 원의 크기)
                hoverinfo="label+percent+value",
                textinfo='label+percent',  # 내부에 레이블 표시
                textfont=dict(size=12, color='#FFFFFF', family='Arial Black'), 
                marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
                pull=[0.1 if i == values.idxmax() else 0 for i in range(len(values))]
            )])

            # 레이아웃 설정
            fig.update_layout(
                showlegend=False,  # 범례 X
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                font=dict(color='#000000'),
                margin=dict(t=0, b=0, l=0, r=0)
            )

            fig.update_traces(
                hoverinfo="label+percent+value",
                textinfo="label+percent",
                marker=dict(line=dict(color='#FFFFFF', width=1))
            )

        else:
            geojson_file_path = './data/kor_geomap.json'
            with open(geojson_file_path, 'r', encoding = 'utf-8') as f:
                geojson_data = json.load(f)
            
            featureidkey = 'properties.CTP_KOR_NM' if category == 'KforeignSpeech' else 'properties.CTP_ENG_NM'

            fig = px.choropleth(
                subcategory_distribution,
                geojson=geojson_data,
                locations='label',
                color = 'count',
                color_continuous_scale='greens',
                range_color = (0, max(subcategory_distribution['count'])),
                featureidkey=featureidkey,  # GeoJSON 파일의 속성 이름과 일치해야 함
                labels={'count': 'Count'}
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                margin={"r":0, "t":0, "l":0, "b":0},
                height = 500
                )
            
        # 차트 렌더링
        st.plotly_chart(fig)

    # 날짜별 누적 분포를 그려내는 함수 (DB 현황 보는 부분)
    @staticmethod
    def plot_datewise_CDF(datewise_CDF, language, category):
        if language == None:
            language = 'Total'
        if category == None:
            category = ''

        fig = go.Figure()
        
        # 누적 라인 차트
        fig.add_trace(go.Scatter(
            x=datewise_CDF['time'],
            y=datewise_CDF['cumulative'],
            mode='lines',
            line=dict(color='#207a8f', width=4),
            showlegend=False
        ))
        
        # 점 추가
        fig.add_trace(go.Scatter(
            x=datewise_CDF['time'],
            y=datewise_CDF['cumulative'],
            mode='markers',
            marker=dict(
                color='red',
                size=12,
                symbol='circle',
                line=dict(color='black', width=2)
            ),
            name='Update Point'
        ))

        # 레이아웃 수정
        fig.update_layout(
            title={
                'text': f'{language} DB Status' if category == '' else f'{category} DB Status',
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='Date',
            yaxis_title='Cumulative Count',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='gray'),
            xaxis=dict(showgrid=True, gridcolor='gray'),
            font=dict(size=14)
        )

        fig.update_traces(marker=dict(size=8),
                        selector=dict(mode='markers'))

        st.plotly_chart(fig)

    # duration 에 대한 histogram
    # 사용 용도 2가지
    # 1) 한국어/영어 각각에 대한 duration histogram 동일한 차트 위에서 다른 색으로 시각화 : 데이터 프레임 2개 인자로
    # 2) 특정 카테고리 선택 시, 그것 하나에 대한 duration histogram 만 시각화 : 데이터 프레임 1개만 인자로
    @staticmethod
    def plot_duration_hist(kor_df, eng_df, kor_df_label='Korean', eng_df_label='English', category_label = None):
        # 40초 이하의 데이터만 필터링
        kor_df = kor_df[kor_df['duration'] <= 40]
        if eng_df is not None:
            eng_df = eng_df[eng_df['duration'] <= 40]
        
        # 첫 번째 데이터프레임 히스토그램
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=kor_df['duration'], 
            nbinsx=100, 
            name=kor_df_label,
            marker_color='#008080',
            opacity=0.75
        ))
        
        # 두 번째 데이터프레임 히스토그램 (인자로 입력된 것 없으면, 하나의 히스토그램만 뜸)
        if eng_df is not None:
            fig.add_trace(go.Histogram(
                x=eng_df['duration'], 
                nbinsx=100, 
                name=eng_df_label,
                marker_color='#005F73',
                opacity=0.75
            ))

        fig.update_layout(
            barmode='overlay' if eng_df is not None else 'relative',  # 2개의 히스토그램(한국어 + 영어 각각)을 겹쳐서 표시
            title=dict(
                text="Duration Comparison" if eng_df is not None else f"{category_label}",
                font=dict(size=20, color='DarkSlateGrey'),
                x=0.5  # 중앙 정렬
            ),
            xaxis=dict(
                title=dict(text='Duration', font=dict(size=16, color='DarkSlateGrey')),
                tickfont=dict(size=12, color='DarkSlateGrey')
            ),
            yaxis=dict(
                title=dict(text='Frequency', font=dict(size=16, color='DarkSlateGrey')),
                tickfont=dict(size=12, color='DarkSlateGrey')
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=10, r=10, t=30, b=0)  # 마진 조정
        )

        fig.update_traces(
            hoverinfo="x+y",
            marker=dict(line=dict(width=0.5, color='DarkSlateGrey'))
        )

        st.plotly_chart(fig)

    # 특정 단어가 얼마나 자주 출현하는지 그 빈도수 시각화 
    @staticmethod
    def plot_frequency_hist(frequency_df, top_K = 30):
        frequency_df = frequency_df.head(top_K)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=frequency_df['word'],
            y=frequency_df['frequency'],
            marker=dict(
                color=frequency_df['frequency'],
                colorscale=[[0, 'rgb(34, 116, 165)'], [1, 'rgb(61, 175, 168)']],
                showscale=True
            ),
            text=frequency_df['frequency'],
            textposition='outside'
        ))

        fig.update_layout(
            title='Word Frequency',
            title_font=dict(size=24, family='Arial', color='black'),
            xaxis=dict(
                title='Words',
                titlefont=dict(size=18, family='Arial', color='black'),
                tickfont=dict(size=14, family='Arial', color='black'),
                tickangle=45
            ),
            yaxis=dict(
                title='Frequency',
                titlefont=dict(size=18, family='Arial', color='black'),
                tickfont=dict(size=14, family='Arial', color='black'),
                gridcolor='rgba(200,200,200,0.5)'
            ),
            plot_bgcolor='white',
            bargap=0.2,
            bargroupgap=0.1
        )

        st.plotly_chart(fig)

    # 모달안에 추가되는 워드 클라우드 시각화
    @staticmethod
    def plot_frequency_wordcloud(frequency_df):
        word_freq_dict = dict(zip(frequency_df['word'], frequency_df['frequency']))
        font_path = './data/korean_font.ttf'
        wordcloud = WordCloud(
            font_path=font_path,
            width=800, 
            height=400, 
            background_color='white', 
            colormap='GnBu',  # 푸른색 계열의 색상 맵
            max_words=200,  # 최대 단어 수
            relative_scaling=0.8,  # 단어 크기 (빈도수에 따른 크기)
            contour_width=3,
            contour_color='black'
        ).generate_from_frequencies(word_freq_dict)

        # 워드 클라우드 시각화
        plt.figure(figsize=(10, 6), dpi=300)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off') 
        st.pyplot(plt)
    
    # 파형 시각화
    @staticmethod
    def plot_waveform(y, sr):
        fig, ax = plt.subplots()
        librosa.display.waveshow(y, sr=sr, ax=ax)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('amplitude')
        st.pyplot(fig)

    # 스펙트로그램 시각화
    @staticmethod
    def plot_spectrogram(y, sr):
        fig, ax = plt.subplots()
        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
        img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', ax=ax)
        fig.colorbar(img, ax=ax, format='%+2.0f dB')
        st.pyplot(fig)
