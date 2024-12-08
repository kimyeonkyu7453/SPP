from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import tensorflow as tf
import FinanceDataReader as fdr
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense, LSTM, Conv1D
from keras.losses import Huber
from keras.callbacks import EarlyStopping, ModelCheckpoint, Callback
from tensorflow.keras.optimizers import Adam
import os

app = Flask(__name__)
progress = 0  # 진행률 추적을 위한 전역 변수

# 진행률을 반환하는 API
@app.route('/progress')
def get_progress():
    return jsonify({'progress': progress})

# 진행률 업데이트 콜백 클래스
class ProgressCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        global progress
        progress = int((epoch + 1) / self.params['epochs'] * 100)

# 주식 예측 API
@app.route('/predict_stock')
def predict_stock():
    global progress
    progress = 0  # 진행률 초기화

    # 클라이언트로부터 종목 코드 수신
    code = request.args.get('code')
    if not code:
        return "종목 코드가 필요합니다."

    # 주가 데이터 불러오기
    stock = fdr.DataReader(code)
    scaler_close = MinMaxScaler()
    scaled_close = scaler_close.fit_transform(stock[['Close']])
    df = pd.DataFrame(scaled_close, columns=['Close'])

    # 데이터셋 분리
    x_train, x_test, y_train, y_test = train_test_split(df.drop('Close', axis=1), df['Close'], test_size=0.2, random_state=0, shuffle=False)

    # 윈도우 데이터셋 생성 함수
    def windowed_dataset(series, window_size, batch_size, shuffle):
        series = tf.expand_dims(series, axis=-1)
        ds = tf.data.Dataset.from_tensor_slices(series)
        ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
        ds = ds.flat_map(lambda w: w.batch(window_size + 1))
        if shuffle:
            ds = ds.shuffle(1000)
        ds = ds.map(lambda w: (w[:-1], w[-1]))
        return ds.batch(batch_size).prefetch(1)

    WINDOW_SIZE = 20
    BATCH_SIZE = 64
    train_data = windowed_dataset(y_train, WINDOW_SIZE, BATCH_SIZE, True)
    test_data = windowed_dataset(y_test, WINDOW_SIZE, BATCH_SIZE, False)

    # 모델 정의
    model = Sequential([
        Conv1D(filters=32, kernel_size=5, padding="causal", activation="relu", input_shape=[WINDOW_SIZE, 1]),
        LSTM(16, activation='tanh'),
        Dense(16, activation="relu"),
        Dense(1),
    ])

    model.compile(loss=Huber(), optimizer=Adam(0.0005), metrics=['mse'])
    earlystopping = EarlyStopping(monitor='val_loss', patience=20)
    filename = os.path.join('tmp', 'checkpoint.weights.h5')
    checkpoint = ModelCheckpoint(filename, save_weights_only=True, save_best_only=True, monitor='val_loss', verbose=1)

    # 모델 학습
    history = model.fit(
        train_data, 
        validation_data=(test_data), 
        epochs=100, 
        callbacks=[checkpoint, earlystopping, ProgressCallback()]
    )
    model.load_weights(filename)

    # 미래 30일 예측
    def forecast_windowed_dataset(series, window_size, batch_size):
        series = tf.expand_dims(series, axis=-1)
        ds = tf.data.Dataset.from_tensor_slices(series)
        ds = ds.window(window_size, shift=1, drop_remainder=True)
        ds = ds.flat_map(lambda w: w.batch(window_size))
        return ds.batch(batch_size).prefetch(1)

    forecast = []
    input_series = np.asarray(y_test[-WINDOW_SIZE:])

    for day in range(30):
        input_data = forecast_windowed_dataset(input_series, WINDOW_SIZE, BATCH_SIZE)
        prediction = model.predict(input_data)
        forecast.append(prediction[0, 0])
        input_series = np.append(input_series[1:], prediction[0, 0])

    # 예측 결과를 원래 가격대로 변환
    forecast = scaler_close.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()
    actual_prices = scaler_close.inverse_transform(np.array(y_test).reshape(-1, 1)).flatten()

    # 예측 날짜 생성
    last_date = stock.index[-1]
    forecast_dates = pd.date_range(last_date, periods=30, freq='B')  # 30일 예측

    # Plotly로 캔들스틱 차트 생성
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Candlestick(
            x=stock.index,
            open=stock['Open'],
            high=stock['High'],
            low=stock['Low'],
            close=stock['Close'],
            increasing_line_color='blue',
            decreasing_line_color='red',
            name="가격",
            increasing_line_width=2,
            decreasing_line_width=2,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=forecast_dates, y=forecast, mode='lines', name='예측 가격'),
        secondary_y=False,
    )

    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="가격 (KRW)",
        hovermode="x unified",
        xaxis=dict(
            rangeslider_visible=True,
            type='date',
            range=['2000-01-01', stock.index[-1].strftime('%Y-%m-%d')],
        ),
        yaxis=dict(
            range=[min(actual_prices) * 0.95, max(actual_prices) * 1.05],
            ticks="outside",
            ticklen=5
        ),
        dragmode='zoom',
        plot_bgcolor='white',
        xaxis_rangeslider=dict(visible=True, thickness=0.05),
        autosize=True,
    )

    fig_html = fig.to_html(full_html=False)

    # HTML 템플릿 렌더링
    return render_template('prediction_result.html', stock_code=code, plot=fig_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
