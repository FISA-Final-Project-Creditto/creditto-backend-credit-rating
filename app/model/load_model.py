# pkl로 저장된 credit_model.pkl 모델과 scaler.pkl을 로드
# 머신로닝 모델 유지/로드 관련 코드 모듈

import pickle
from app.config.config import settings

# 모델, 스케일러 로딩
def load_credit_model():
    with open(settings.MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model

def load_scaler():
    with open(settings.SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return scaler