import os
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st


# 모든 데이터 여기서 관리
class DataManager:
    def __init__(self):
        # 전체적인 메타 데이터 불러오기
        self.__data_df = self.load_df()

        # 언어로 분류된 데이터 프레임
        self.__language_distribution = self.__set_language_distribution()

        ### 각 언어 내에 포함된 카테고리
        self.__language_components = self.__set_language_components()
        
        # 카테고리 별 간략한 설명
        self.__category_explanations = self.__set_category_explanations()

        # 카테고리별 분포
        self.__category_distribution = self.__set_category_distribution()

        # 서브카테고리를 갖는 카테고리의 목록
        self.__categories = self.__set_categories()

        # 카테고리 내부에서의 서브 카테고리 분포
        self.__subcategory_distributions = {}

        # 서브 카테고리 분포 세팅
        for category in self.__categories:
            self.__subcategory_distributions[category] = self.__set_subcategory_distribution(category)

    #data 관련 csv 파일 불러오기
    @st.cache_data(persist = 'disk')
    def load_df(__self, route = './data/meta__data.csv'):
        if os.path.exists(route):
            df = pd.read_csv(route)
            print("데이터 로딩중...")
            return df
        else:
            return None
        
    # language 카테고리의 분포 업데이트
    @st.cache_data(persist = 'disk')
    def __set_language_distribution(__self):
        df = __self.__data_df['language'].value_counts().to_frame(name = 'count')
        df = df.reset_index().rename(columns = {'language' : 'label'})
        df['count'] = df['count'].astype(int)
        return df
    
    # kor/english 내부 sub 카테고리 정리 위한 setter
    @st.cache_data(persist = 'disk')
    def __set_language_components(__self):
        return __self.__data_df.groupby('language')['category'].apply(lambda x: x.unique())
    
    # category 별 설명을 담는 데이터 프레임
    def __set_category_explanations(self):
        return pd.read_csv('./data/cat_explanation.csv')
    
    # 주 카테고리의 분포 업데이트(새로운 데이터 들어왔을 때)
    @st.cache_data(persist = 'disk')
    def __set_category_distribution(__self):
        df = __self.__data_df['category'].value_counts().to_frame(name = 'count')
        df = df.reset_index().rename(columns = {'category' : 'label'})
        df['count'] = df['count'].astype(int)
        return df
    
    # subcategory 분류가 있는 카테고리 설정
    @st.cache_data(persist = 'disk')
    def __set_categories(__self):
        category_list = __self.__data_df[__self.__data_df['subcategory'] != '-']['category'].unique()
        return category_list
    
    # 하위 카테고리 중 하나의 분포 업데이트
    @st.cache_data(persist = 'disk')
    def __set_subcategory_distribution(__self, category):
        df = __self.__data_df[__self.__data_df['category']==category]['subcategory'].value_counts().to_frame(name = 'count')
        df = df.reset_index().rename(columns = {'subcategory' : 'label'})
        df['count'] = df['count'].astype(int)
        return df


    def get_language_distribution(self):
        return self.__language_distribution
    
    # kor/english 의 내부 sub 카테고리들
    def get_language_components(self, language=None):
        if language != None:
            return self.__language_components[language].tolist()
        else:
            every_components = np.concatenate(self.__language_components.values)
            return every_components.tolist()
    
    # category 별 설명을 가진 데이터 프레임 가져옴
    def get_category_explanations(self, category):
        explanation = self.__category_explanations[self.__category_explanations['category'] == category]['explanation']
        if explanation.empty:
            return None
        return explanation.iloc[0]
    
    def get_category_distribution(self, language = None):
        if language == None:
            return self.__category_distribution
        # 추가 부분
        else:
            categories = self.get_language_components(language)
            df = self.__category_distribution.loc[self.__category_distribution['label'].isin(categories)]
            return df
    
    # sub_categories 가져오기
    def get_categories(self):
        return self.__categories
    
    # sub_distributions 중에서 하나만 지정해서 가져오기
    def get_subcategory_distribution(self, category):
        return self.__subcategory_distributions[category]
        
    # 특정 날짜별 추가된 데이터 개수, 누적개수 리턴
    def get_daily_counts(self, min_date = None, max_date = None, language = None, category = None):
        if language == None:
            pre_date_df = self.__data_df.copy()
        else:
            pre_date_df = self.__filter_df(language, category)

        pre_date_df = pre_date_df['time'].value_counts().to_frame(name = 'count')
        pre_date_df = pre_date_df.sort_index()
        pre_date_df['cumulative'] = pre_date_df['count'].cumsum()

        pre_date_df = pre_date_df.reset_index()
        pre_date_df.rename(columns={'index' : 'time'},inplace=True)

        if min_date != None and max_date != None:
            # 'time' 열을 datetime으로 변환하고, date만 추출하여 비교
            date_df = pre_date_df[(pd.to_datetime(pre_date_df['time']).dt.date >= min_date) & (pd.to_datetime(pre_date_df['time']).dt.date <= max_date)]
        else:
            date_df = pre_date_df
        return date_df
        
    # DB 에 있는 데이터량의 변화에 대한 통계 정보 (증가량, 변화율)
    def calc_change_stats(self, date_df):
        start_cumulative = date_df['cumulative'].iloc[0]
        end_cumulative = date_df['cumulative'].iloc[-1]

        change_rate = (end_cumulative - start_cumulative)/start_cumulative*100
        increment = end_cumulative - start_cumulative
        return increment, change_rate
        
    # 원본 데이터 프레임을 필터링하는 용도
    def __filter_df(self, language=None, category=None):
        if category == None:
            filtered_df = self.__data_df[self.__data_df['language'] == language]
            return filtered_df
        elif category != None:
            filtered_df = self.__data_df[self.__data_df['category'] == category]
            return filtered_df
        
    # 전체에 대한 histogram 그릴때는 필요없음.
    def get_duration_counts(self, language=None, category=None):
        duration_df = self.__filter_df(language, category)['duration'].to_frame()
        return duration_df

    # duration 과 관련한 통계 정보
    def calc_duration_stats(self, duration_df):
        total_time = round(duration_df['duration'].sum()/3600)
        mean_time = round(duration_df['duration'].mean(), 1)
        return total_time, mean_time

    # 한국어/영어의 평균 단어 개수 OR 특정 카테고리의 평균 단어 개수
    def get_word_count(self, category=None):
        if category==None:
            kor_df = self.__filter_df(language = 'korean')
            eng_df = self.__filter_df(language = 'english')
            return round(kor_df.word_count.mean(), 1), round(eng_df.word_count.mean(), 1)
        else:
            specified_df = self.__filter_df(category = category)
            return round(specified_df.word_count.mean(), 1)
    
    # 단어의 빈도수 계산    
    @st.cache_data
    def get_word_freq(__self, language, category):
        if category == None:
            df = __self.__filter_df(language=language)
        else:
            df = __self.__filter_df(category=category)
        all_words = " ".join(df['final_script'].astype(str)).split()
        word_count = Counter(all_words)
        word_count_df = pd.DataFrame(word_count.items(), columns=['word', 'frequency'])
        word_count_df.sort_values(by = 'frequency', ascending = False, inplace=True)
        return word_count_df