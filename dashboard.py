from datetime import datetime

import pandas as pd
import librosa
import librosa.display
import streamlit as st
from streamlit_modal import Modal

from manager.audio_manager import AudioManager
from manager.data_manager import DataManager
from tool.render_tool import RenderTool
from tool.visual_tool import VisualTool

st.set_page_config(
    page_title = 'Dashboard',
    page_icon = "📈",
    layout = 'wide',
    initial_sidebar_state= 'expanded'
)

st.logo(image='./data/logo.png')

# 금일 날짜 표시
today_date = datetime.now().strftime("%Y-%m-%d")
st.sidebar.markdown(f"### {today_date}")

# 사이드 바에 Data/Log 중 무엇을 볼지 정의
with st.sidebar:
    option = RenderTool.render_option_menu()

# 세션 별 데이터 관리하는 관리자 객체 생성 (세션이 새로 고침되면 객체 다시 생성)
if 'data_manager' not in st.session_state:
    st.session_state['data_manager'] = DataManager()

if 'audio_manager' not in st.session_state:
    st.session_state['audio_manager'] = AudioManager()

if option == 'Data Navigator':
    # 전체 화면 분할
    col0, col1 = st.columns((8, 2))
    with col0:
        # 시각화 부분
        vis_placeholder = st.empty()
        with vis_placeholder.container():
            RenderTool.render_space(523)
        st.markdown('---')
        # 검색 옵션 부분
        nav_placeholder_0, nav_placeholder_1, nav_placeholder_2, nav_placeholder_3 = RenderTool.render_layout([2,3,2,2])
        nav_option = nav_placeholder_0.radio('Navigating Option 🔍', ['Status', 'Detail'])
        st.markdown('---')
    with col1:
        # 변화랑/통계 정보 전달 위한 placeholder (위쪽)
        stats_upper_placeholder = st.empty()
        
        # 변화량/통계 정보 전달 위한 placeholder (아래쪽)
        stats_lower_placeholder = st.empty()
    
    # DB 현황 보고자 할 경우
    if nav_option == 'Status':
        # 날짜 옵션
        with nav_placeholder_1.container():
            start_date = st.date_input('Start date', min_value=pd.to_datetime('2023-08-17'), value = pd.to_datetime('2023-08-17'), max_value=pd.to_datetime(today_date))
            end_date = st.date_input('End date', min_value=pd.to_datetime('2023-08-17'),value = 'today', max_value=pd.to_datetime(today_date))
                
        # 언어 옵션
        with nav_placeholder_2:
            selected_language = st.radio("Language",['Total', 'Korean', 'English'])
            selected_language = selected_language.lower()
            # Total 선택 시, 선택된 언어 = None
            if selected_language == 'total':
                selected_language = None
        # 언어 옵션 중 한국어/영어 선택 시
        if selected_language != None:
            # 언어 옵션에 해당하는 카테고리 옵션
            with nav_placeholder_3.container():
                selected_category = st.selectbox(
                                        "Category",
                                        st.session_state['data_manager'].get_language_components(selected_language),
                                        index = None
                                    )
            # 선택한 언어 내부의 카테고리 분포 시각화 (우측 하단)
            with stats_lower_placeholder.container():
                VisualTool.plot_cat_partial(st.session_state['data_manager'].get_category_distribution(), st.session_state['data_manager'].get_language_components(selected_language))
        
        else:
            # 전체 언어 선택했을 때, 한국/영어 데이터 비율 시각화 (우측 하단)
            selected_category = None
            with stats_lower_placeholder.container():
                VisualTool.plot_language_dist(st.session_state['data_manager'].get_language_distribution())
        
        # 선택한 날짜, 언어, 카테고리에 따른 데이터의 변화량 시각화
        with vis_placeholder.container():
            VisualTool.plot_datewise_CDF(st.session_state['data_manager'].get_daily_counts(min_date = start_date, max_date = end_date, language = selected_language, category = selected_category), selected_language, selected_category)

        # 선택한 날짜, 언어, 카테고리에 따른 데이터의 변화량/변화율 수치
        with stats_upper_placeholder.container():
            increment, change_rate = st.session_state['data_manager'].calc_change_stats(st.session_state['data_manager'].get_daily_counts(min_date = start_date, max_date = end_date, language = selected_language, category = selected_category))
            col0, col1 = st.columns((2,8))
            with col1:
                st.metric(label = 'Change Stat', value = f"{increment/1000} K", delta = f"{change_rate:.2f}%")

    # 상세 정보 보고자 할 경우
    elif nav_option == 'Detail':
        
        # 상세 정보 중 '분류' 볼지, '콘텐츠' 볼지 선택
        with nav_placeholder_1:
            info_option = st.radio('Select', ['Classification', 'Content'])
        
        with nav_placeholder_2:
            # '분류' 선택 시, 카테고리/하위카테고리 정보 선택 가능
            if info_option == 'Classification':
                search_option = st.radio('View', ['Category', 'Subcategory'])

            # '콘텐츠' 선택 시, 스크립트/duration 정보 선택 가능
            elif info_option == 'Content':
                search_option = st.radio('View', ['Script', 'Wav'])
        
        # '분류' 중 카테고리 선택 시,
        if search_option == 'Category':
            # 카테고리 중 어떤 걸 볼지, 한국어/영어 내부에서 카테고리 선택 가능
            with nav_placeholder_3.container():
                search_queries_kor = st.multiselect('Korean', st.session_state['data_manager'].get_language_components('korean'))
                search_queries_eng = st.multiselect('English', st.session_state['data_manager'].get_language_components('english'))

            # 메인 시각화 부분 : 한국어/영어 각각 내부의 카테고리 별 분포 시각화
            with vis_placeholder.container():
                col0, col1 = st.columns(2)
                with col0:    
                    VisualTool.plot_cat_dist(st.session_state['data_manager'].get_category_distribution("korean"), search_queries_kor, '한국어')
                with col1:
                    VisualTool.plot_cat_dist(st.session_state['data_manager'].get_category_distribution('english'), search_queries_eng, '영어') 
            # 선택한 한국어 카테고리(데이터 셋)에 대한 간략한 설명
            with stats_upper_placeholder.container():
                st.markdown('##### 한국어 분류 정보')
                if search_queries_kor != None:
                    for query in search_queries_kor:
                        RenderTool.render_border_chat(query, st.session_state['data_manager'].get_category_explanations(query))
                # 한국어/영어 설명 간 구분자
                st.markdown('---')
            # 선택한 영어 카테고리(데이터 셋)에 대한 간략한 설명
            with stats_lower_placeholder.container():
                st.markdown('##### 영어 분류 정보')
                if search_queries_eng != None:
                    for query in search_queries_eng:
                        RenderTool.render_border_chat(query, st.session_state['data_manager'].get_category_explanations(query))
        # '분류' 중 하위 카테고리 선택 시
        elif search_option == 'Subcategory':
            # 어떤 카테고리 내부의 '하위 카테고리 분포' 를 시각화 할지 선택 (최대 2개까지 선택 가능)
            with nav_placeholder_3.container():
                categories = st.session_state['data_manager'].get_categories()
                selected_categories = st.multiselect(
                    'View Categories (max 2):',
                    categories,
                    default = None,
                    help = 'You can select up to 2 options'
                )
            # 선택한 카테고리 내부의 하위 카테고리 분포 파악 가능
            with vis_placeholder.container():
                # 개수 제한 (2개 이하)
                if len(selected_categories) > 2:
                    st.error('You can select up to 2 categories')
                    selected_categories = selected_categories[:2]
                
                # 하나라도 선택 시작되면 바로 시각화
                if len(selected_categories) > 0:
                    columns = st.columns(len(selected_categories))

                    for col, category in zip(columns, selected_categories):
                        with col:
                            st.markdown(f"### {category}")
                            if category == 'DialectSpeech' or category == 'KforeignSpeech':
                                VisualTool.plot_subcategory_dist(st.session_state['data_manager'].get_subcategory_distribution(category), category)
                            else:
                                VisualTool.plot_subcategory_dist(st.session_state['data_manager'].get_subcategory_distribution(category))

        # '콘텐츠' 중 스크립트 정보 선택 시
        elif search_option == 'Script':
            # script 를 선택했을 때, 추가로 언어/카테고리 선택 가능
            with nav_placeholder_3.container():
                selected_language = st.selectbox("Language", ['korean', 'english'], index = 0)
                selected_category = st.selectbox('Category', st.session_state['data_manager'].get_language_components(selected_language), index = None)

            # 평균 단어 개수 (한국 & 영어)
            with stats_upper_placeholder.container():
                inner_placeholder = st.empty()

                # 한국어/영어의 평균 단어 개수
                kor_count_mean, eng_count_mean = st.session_state['data_manager'].get_word_count()
                col0, col1 = st.columns((0.3, 9.7))
                with col1:
                    st.metric('한국어 평균 단어 개수', kor_count_mean)
                    st.metric('영어 평균 단어 개수', eng_count_mean)

                # 선택한 카테고리 평균 단어 개수
                if selected_category != None:
                    with inner_placeholder.container():
                        RenderTool.render_border_text(selected_category, st.session_state['data_manager'].get_word_count(selected_category))
                        RenderTool.render_space(50)
            # 워드 클라우드 + 빈도수 바 그래프 시각화
            with vis_placeholder.container():
                # 모달 정의
                modal = Modal(key = 'wordcloud', title = '<WordCloud>')
                if st.button('WordCloud'):
                    modal.open()
                # 단어 빈도수 시각화 바 그래프
                VisualTool.plot_frequency_hist(st.session_state['data_manager'].get_word_freq(selected_language, selected_category))
                # 모달 오픈 시, 워드 클라우드 시각화
                if modal.is_open():
                    with modal.container():
                        # wordcloud
                        VisualTool.plot_frequency_wordcloud(st.session_state['data_manager'].get_word_freq(selected_language, selected_category))
        
        # '콘텐츠' 중, duration 정보 선택 시       
        elif search_option == 'Wav':
            # 어떤 카테고리의 duration 정보를 볼 지 선택 가능
            with nav_placeholder_3.container():
                selected_language = st.selectbox("Language", ['korean', 'english'], index = 0)
                selected_category = st.selectbox('Category', st.session_state['data_manager'].get_language_components(selected_language), index = None)
            # duration 관련 통계 정보 (총 시간, 평균 시간)
            with stats_upper_placeholder.container():
                inner_placeholder = st.empty()
                kor_duration_total, kor_duration_mean = st.session_state['data_manager'].calc_duration_stats(st.session_state['data_manager'].get_duration_counts(language='korean'))
                eng_duration_total, eng_duration_mean = st.session_state['data_manager'].calc_duration_stats(st.session_state['data_manager'].get_duration_counts(language='english'))
                col0, col1 = st.columns((0.3, 9.7))
                with col1:
                    st.metric(label = '한국어 시간 총/평균', value = f"{kor_duration_total}H/{kor_duration_mean}s")
                    st.metric(label = '영어 시간 총/평균', value = f"{eng_duration_total}H/{eng_duration_mean}s")
            # 한국어/영어 duration 시각화 (카테고리 선택 X 일 때)
            if selected_category == None:
                with vis_placeholder.container():
                    VisualTool.plot_duration_hist(
                        st.session_state['data_manager'].get_duration_counts(language = 'korean'),
                        st.session_state['data_manager'].get_duration_counts(language = 'english')
                    )
            # 특정 카테고리 선택 했을 경우
            elif selected_category != None:
                # 히스토그램 시각화
                with vis_placeholder.container():
                    VisualTool.plot_duration_hist(st.session_state['data_manager'].get_duration_counts(category = selected_category), None, category_label=selected_category)
                # 선택된 분류에 대한 총/평균 시간
                with inner_placeholder.container():
                    _, specific_duration_mean = st.session_state['data_manager'].calc_duration_stats(st.session_state['data_manager'].get_duration_counts(category=selected_category))
                    RenderTool.render_border_text(selected_category, specific_duration_mean)
                    RenderTool.render_space(50)

# 증강 부분
elif option == 'Augmentation':
    # 업로드할지, 녹음할지, 여러개 한번에 증강할지
    upload, record, multi_augmentation = st.tabs(['Upload ⬆️', 'Record 🎙️', 'MultiAugmentation'])

    # 'upload' 와 'record' 부분에서 같은 레이아웃임에도 따로 정의한 이유 : tab 을 바꿔도 레이아웃이 동일하게 유지됨
    with upload:
        # 위의 시각화 부분 미리 예약 걸어두는 부분
        upload_upper_placeholder = st.empty()
        with upload_upper_placeholder.container():
            RenderTool.render_space(523)
        st.markdown('---')
        # 옵션 선택하는 부분의 레이아웃
        upload_placeholder_0, upload_placeholder_1, upload_placeholder_2 = RenderTool.render_layout([3,3,1])
    with record:
        # 위의 시각화 부분 미리 예약 걸어두는 부분
        record_upper_placeholder = st.empty()
        with record_upper_placeholder.container():
            RenderTool.render_space(523)
        st.markdown('---')
        record_placeholder_0, record_placeholder_1, record_placeholder_2 = RenderTool.render_layout([3,3,1])

    # 음성 파일 업로드 시
    with upload:
        # 오디오 업로드 하는 부분
        with upload_placeholder_0.container():
            uploaded_file = st.session_state['audio_manager'].upload_audio()
        # 오디오 업로드 되면, 나머지 옵션 띄우기
        if uploaded_file is not None:
            y, sr = librosa.load(uploaded_file, sr = None)
            # 증강 옵션
            with upload_placeholder_1.container():
                # st.form 으로 묶어서 강제 재로드 막기
                with st.form(key='upload'):
                    with st.expander('배경/가우시안 소음 추가'):
                        noise_min_snr, noise_max_snr, noise_min_amplitude, noise_max_amplitude = st.session_state['audio_manager'].show_noise_option('upload')
                    with st.expander('속도/피치/볼륨 조정'):
                        time_stretch_min_rate, time_stretch_max_rate, pitch_shift_min_semitones, pitch_shift_max_semitones, gain_min_db, gain_max_db = st.session_state['audio_manager'].show_tuning_option('upload')
                    _, col = st.columns((8.8, 1.2))
                    with col:
                        # form_submit_button 이 트리거로 이 버튼이 실제로 눌리면, 재로드 됨
                        create = st.form_submit_button(label='생성')
                        if create: # 증강 옵션 세팅
                            augment = st.session_state['audio_manager'].set_augmentation(
                                noise_min_snr, noise_max_snr,
                                noise_min_amplitude, noise_max_amplitude,
                                time_stretch_min_rate, time_stretch_max_rate,
                                pitch_shift_min_semitones, pitch_shift_max_semitones,
                                gain_min_db, gain_max_db
                            )
                            # 실제 증강 수행
                            st.session_state['audio_manager'].generate_augmentations(y, sr, 1, augment, uploaded=True)
            
            # 원본/증강 오디오를 어떤 시각화 방식으로 볼 지 선택
            with upload_placeholder_2.container():
                view_option = st.radio('View Option', ['Waveform', 'Spectrogram'])
            
            with upload_upper_placeholder.container():            
                # 파형 선택 시, 시각화
                if view_option == 'Waveform':
                    before, after = st.columns(2) # 증강 전후 파형 비교
                    try:
                        with before:
                            st.subheader('원본 파형 (Waveform)')
                            VisualTool.plot_waveform(y, sr)
                            st.session_state['audio_manager'].play_audio(audio_input = uploaded_file)
                        with after: 
                            st.subheader('증강된 파형 (Waveform)')
                            VisualTool.plot_waveform(st.session_state['audio_manager'].get_uploaded_augmentation(), sr)
                            st.session_state['audio_manager'].play_audio(augmented_audio=st.session_state['audio_manager'].get_uploaded_augmentation(), sr=sr)
                    except Exception as e:
                        with after:
                            st.info('생성 버튼을 누르세요', icon = 'ℹ️')
                # 스펙트로그램 선택 시, 시각화
                elif view_option == 'Spectrogram':
                    before, after = st.columns(2) # 증강 전후 스펙트로그램 비교
                    try:
                        with before:
                            st.subheader('원본 스펙트로그램')
                            VisualTool.plot_spectrogram(y, sr)
                        with after:
                            st.subheader('증강된 스펙트로그램')
                            VisualTool.plot_spectrogram(st.session_state['audio_manager'].get_uploaded_augmentation(), sr)
                    except Exception as e:
                        with after:
                            st.info('생성 버튼을 누르세요', icon = 'ℹ️')
    # 음성 파일 녹음          
    with record:
        # 녹음 시작/종료
        with record_placeholder_0.container():
            recorded_audio = st.session_state['audio_manager'].record_audio()
        # 녹음이 완료 되면, 
        if recorded_audio is not None:
            # 녹음된 음성 후처리
            y, sr, wav_io = st.session_state['audio_manager'].process_record(recorded_audio)
            # 증강 옵션 선택
            with record_placeholder_1.container():
                # 무차별 재로드 방지 위해 st.form 사용
                with st.form(key='record'):
                    with st.expander('배경/가우시안 소음 추가'):
                        noise_min_snr, noise_max_snr, noise_min_amplitude, noise_max_amplitude = st.session_state['audio_manager'].show_noise_option('record')
                    with st.expander('속도/피치/볼륨 조정'):
                        time_stretch_min_rate, time_stretch_max_rate, pitch_shift_min_semitones, pitch_shift_max_semitones, gain_min_db, gain_max_db = st.session_state['audio_manager'].show_tuning_option('record')
                    _, col = st.columns((8.8, 1.2))
                    with col:
                        create = st.form_submit_button(label='생성')
                        if create: # 증강 옵션 세팅
                            augment = st.session_state['audio_manager'].set_augmentation(
                                noise_min_snr, noise_max_snr,
                                noise_min_amplitude, noise_max_amplitude,
                                time_stretch_min_rate, time_stretch_max_rate,
                                pitch_shift_min_semitones, pitch_shift_max_semitones,
                                gain_min_db, gain_max_db
                            )
                            # 실제 증강 수행
                            st.session_state['audio_manager'].generate_augmentations(y, sr, 1, augment)

            # 원본/증강 오디오 어떤 시각화를 볼지 선택 
            with record_placeholder_2.container():
                view_option = st.radio('View Option', ['Waveform', 'Spectrogram'], key = 'record_view')
            
            # 원본/증강 오디오 시각화 부분
            with record_upper_placeholder.container():
                # 파형 시각화
                if view_option == 'Waveform':
                    before, after = st.columns(2) # 증강 전후 파형 비교
                    try:
                        with before:
                            st.subheader('원본 파형 (Waveform)')
                            VisualTool.plot_waveform(y, sr)
                            st.session_state['audio_manager'].play_audio(audio_input=wav_io)
                        with after:
                            st.subheader('증강된 파형 (Waveform)')
                            VisualTool.plot_waveform(st.session_state['audio_manager'].get_recorded_augmentation(), sr)
                            st.session_state['audio_manager'].play_audio(augmented_audio=st.session_state['audio_manager'].get_recorded_augmentation(), sr=sr)
                    except Exception as e:
                        with after:
                            st.info('생성 버튼을 누르세요', icon = 'ℹ️')
                # 스펙트로그램 시각화
                elif view_option == 'Spectrogram':
                    before, after = st.columns(2) # 증강 전후 스펙트로그램 비교
                    try:
                        with before:
                            st.subheader('원본 스펙트로그램')
                            VisualTool.plot_spectrogram(y, sr)
                        with after:
                            st.subheader('증강된 스펙트로그램')
                            VisualTool.plot_spectrogram(st.session_state['audio_manager'].get_recorded_augmentation(), sr)
                    except Exception as e:
                        with after:
                            st.info('생성 버튼을 누르세요', icon = 'ℹ️')
    # 다중 증강 탭
    with multi_augmentation:
        st.header("랜덤 증강 오디오 생성기")
        # 파일 업로드
        uploaded_file = st.file_uploader('WAV 파일을 업로드하세요', type=['wav'])
        if uploaded_file is not None:
            y, sr = librosa.load(uploaded_file, sr=None)
            st.session_state['audio_manager'].play_audio(audio_input=uploaded_file)
            
            # 증강 개수 설정
            n_augmentations = st.number_input("증강 파일 개수를 입력하세요", min_value=1, value=5)
            
            if st.button("증강 파일 생성"):
                augmented_audios = st.session_state['audio_manager'].generate_augmentations(y, sr, n_augmentations)
                st.success(f"{n_augmentations}개의 증강 파일이 생성되었습니다.")
                
                # ZIP 파일 다운로드 버튼
                zip_buffer = st.session_state['audio_manager'].download_zip(augmented_audios, sr)
                st.download_button(label="증강 파일 다운로드 (ZIP)", data=zip_buffer, file_name="augmentations.zip", mime="application/zip")