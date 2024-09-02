import io
import random
import zipfile

import librosa
import librosa.display
import pydub
import soundfile as sf
from audiomentations import Compose, AddBackgroundNoise, TimeStretch, PitchShift, Gain, AddGaussianNoise
import streamlit as st
from streamlit_mic_recorder import mic_recorder


# 오디오 관련 관리자 (각종 함수 제공)
class AudioManager:

    def __init__(self):
        # 증강된 업로드된 음성
        self.__uploaded_augmentation = None
        # 증강된 녹음된 음성
        self.__recorded_augmentation = None

    # 녹음
    def record_audio(self):
        recorded_audio = mic_recorder(start_prompt='▶️ Start', stop_prompt='⏹️ Stop', callback=self.__record_callback)
        return recorded_audio
    
    # record_audio 의 call back 함수
    def __record_callback(self):
        if self.__recorded_augmentation is not None:
            self.__recorded_augmentation = None

    # 녹음 후처리 (webm -> wav 변환)
    def process_record(self, record):
        uploaded_file = io.BytesIO(record['bytes'])
        audio_segment = pydub.AudioSegment.from_file(uploaded_file, format = 'webm')
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format='wav')
        wav_io.seek(0)
        y, sr = librosa.load(wav_io, sr = 16000) # sample rate 16000
        return y, sr, wav_io
    
    # recorded_augmentation 가져오기
    def get_recorded_augmentation(self):
        return self.__recorded_augmentation
    
    # 음성 업로드
    def upload_audio(self):
        uploaded_file = st.file_uploader(' ',type = ['wav'], on_change=self.__upload_callback)
        return uploaded_file
    
    # upload_audio 의 call back 함수
    def __upload_callback(self):
        if self.__uploaded_augmentation is not None:
            self.__uploaded_augmentation = None
            
    # uploaded_augmentation 가져오기
    def get_uploaded_augmentation(self):
        return self.__uploaded_augmentation
    
    # audio player
    # 원본 : audio_input 만 입력 / 증강 : audio_input 제외 모든 인자 필요
    def play_audio(self, audio_input = None, augmented_audio = None, sr = None):
        if audio_input:
            st.audio(audio_input, format='audio/wav')
        else:
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, augmented_audio, sr, format='WAV')
            audio_buffer.seek(0)
            st.audio(audio_buffer, format='audio/wav')

    # 증강 시, 노이즈 옵션
    def show_noise_option(self, key):
        return (st.slider("Minimum SNR (Signal to Noise Ratio)", min_value=15, max_value=30, value=17, key=f'{key}_min_snr'),
                st.slider("Maximum SNR", min_value=15, max_value=30, value=25, key=f'{key}_max_snr'),
                st.slider("최소 Noise Amplitude", min_value=0.001, max_value=0.015, value=0.003, step = 0.001, format = '%f', key=f'{key}_min_amp'),
                st.slider("최대 Noise Amplitude", min_value=0.001, max_value=0.015, value=0.007, step = 0.001, format = '%f', key=f'{key}_max_amp'))
    # 증강 시, 속도/피치/볼륨 옵션
    def show_tuning_option(self, key):
        return(st.slider("최소 속도 변화 비율", min_value=0.5, max_value=1.5, value=0.8, key=f'{key}_min_rate'),
               st.slider("최대 속도 변화 비율", min_value=0.5, max_value=1.5, value=1.2, key=f'{key}_max_rate'),
               st.slider("최소 반음", min_value=-12, max_value=0, value=-5, key=f'{key}_min_sem'),
               st.slider("최대 반음", min_value=0, max_value=12, value=5, key=f'{key}_max_sem'),
               st.slider("최소 Gain (dB)", min_value=-30, max_value=0, value=-15, key=f'{key}_min_db'),
               st.slider("최대 Gain (dB)", min_value=0, max_value=30, value=15, key=f'{key}_max_db'))
    # 증강 세팅
    def set_augmentation(self,
        noise_min_snr = None, noise_max_snr = None,
        noise_min_amplitude = None, noise_max_amplitude = None,
        time_stretch_min_rate = None, time_stretch_max_rate = None,
        pitch_shift_min_semitones = None, pitch_shift_max_semitones = None,
        gain_min_db = None, gain_max_db = None
    ):
        p = 1.0 # 내가 지정할 경우, 설정하는대로 반영위해, 1.0 으로 설정
        # 입력된 값이 없을 때
        if noise_min_snr == None:
            noise_min_snr = random.uniform(-10, 20)
            noise_max_snr = random.uniform(noise_min_snr, 20)
            noise_min_amplitude = random.uniform(0.0, 0.008)
            noise_max_amplitude = random.uniform(noise_min_amplitude, 0.015)
            time_stretch_min_rate = random.uniform(0.5, 1.5)
            time_stretch_max_rate = random.uniform(time_stretch_min_rate, 1.5)
            pitch_shift_min_semitones = random.randint(-12, 0)
            pitch_shift_max_semitones = random.randint(0, 12)
            gain_min_db = random.uniform(-30, 0)
            gain_max_db = random.uniform(0, 30)
            p = 0.5 # 랜덤하게 여러개 생성시에는 다양성을 위해 0.5로 설정
        # 증강 세팅
        augment = Compose([
            AddBackgroundNoise(sounds_path='./data/background_noise.wav', min_snr_in_db=noise_min_snr, max_snr_in_db=noise_max_snr, p=p),
            TimeStretch(min_rate=time_stretch_min_rate, max_rate=time_stretch_max_rate, p=p),
            PitchShift(min_semitones=pitch_shift_min_semitones, max_semitones=pitch_shift_max_semitones, p=p),
            Gain(min_gain_in_db=gain_min_db, max_gain_in_db=gain_max_db, p=p),
            AddGaussianNoise(min_amplitude=noise_min_amplitude, max_amplitude=noise_max_amplitude, p=p),
        ])
        return augment
    
    # 실제 증강 수행
    def generate_augmentations(self, y, sr, n_augmentations, augment = None, uploaded = False):
        # 지정된 augment 없으면 랜덤 (= batch 로 증강시)
        if augment == None:
            augmented_audios = []
            for i in range(n_augmentations):
                augment = self.set_augmentation()
                augmented_audio = augment(samples = y, sample_rate = sr)
                augmented_audios.append(augmented_audio)
            return augmented_audios
        else:
            if not uploaded:
                self.__recorded_augmentation = augment(samples = y, sample_rate = sr)
                return self.__recorded_augmentation
            else:
                self.__uploaded_augmentation = augment(samples = y, sample_rate = sr)
                return self.__uploaded_augmentation
    
    # 증강된 오디오 파일 다운
    def download_zip(self, augmented_audios, sr):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for i, audio in enumerate(augmented_audios):
                audio_buffer = io.BytesIO()
                sf.write(audio_buffer, audio, sr, format='WAV')
                audio_buffer.seek(0)
                zf.writestr(f"augmentation_{i+1}.wav", audio_buffer.read())
        zip_buffer.seek(0)
        return zip_buffer
