import streamlit as st

from streamlit_extras.grid import grid
from streamlit_modal import Modal
from streamlit_option_menu import option_menu


# 웹 UI 관련한 것들 관리하는 도구
class RenderTool:
    # 옵션바
    @staticmethod
    def render_option_menu():
        option = option_menu("Menu", ['Data Navigator','Augmentation'],
                            icons = ['compass', 'folder-plus'],
                            menu_icon = 'window-stack',
                            styles={
                            "container": {"padding": "0!important", "background-color": "#fafafa"},
                            "icon": {"color": "black", "font-size": "17px"},
                            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#d3d3d3"},
                            "nav-link-selected": {"background-color": "#a9a9a9"},
                            })
        return option
    # 공간 확보 용도
    @staticmethod
    def render_space(height):
        st.markdown(
            f"""
            <style>
            .spacer {{
                height: {height}px;
            }}
            </style>
            <div class="spacer"></div>
            """,
            unsafe_allow_html=True
        )
    # border 쳐져 있는 텍스트
    @staticmethod
    def render_border_text(text, number):
        st.markdown(
            f"""
            <div style="border: 3px solid #4a93a3; padding: 20px; border-radius: 30px;">
                <p><strong>{text} 평균 </strong></p>
                <h3 style="font-size: 36px;">{number}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    # border 쳐져 있는 chat
    @staticmethod
    def render_border_chat(text_1, text_2):
        st.chat_message('assistant').markdown(
            f"""
            <div style="border: 2px solid #b9d5db; padding: 10px; border-radius: 5px; background-color: #f0f8ff;">
                <strong>{text_1}:</strong> {text_2}
            </div>
            """,
            unsafe_allow_html=True
        )
    # 가로로 몇개로 나눌건지, 그 비율
    @staticmethod
    def render_layout(ratio):
        ph_list = []
        placeholders = grid(ratio)
        for _ in range(len(ratio)):
            ph_list.append(placeholders.empty())
        return *ph_list, # 언패킹하여 리턴

    # 모달 때문에 어쩔 수 없이 일단 남겨놓은 것.
    # st.markdown(
    #     """
    #     <style>
    #     .st-emotion-cache-l6wp7i {
    #         min-width: 700px !important;
    #         width: 700px;
    #         max-width: 800px !important;
    #         position: fixed !important;
    #         top: 50% !important;
    #         left: 50% !important;
    #         transform: translate(-50%, -50%);
    #         display: flex;
    #         flex: 1 1 0%;
    #         flex-direction: column;
    #         min-height: 400px !important;
    #         height: 500px;
    #         max-height: 600px !important; 
    #         overflow-y: auto;
    #     }
    #     </style>
    #     """,
    #     unsafe_allow_html=True
    # )