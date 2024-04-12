from flask import Flask, render_template, url_for, request
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
import functions as fn
import pandas as pd
from sklearn.metrics import mean_squared_error
import numpy as np

# Устанавливаем стандартную тему Plotly
pio.templates.default = 'plotly'

app = Flask(__name__)

# Глобальная переменная для хранения пути к HTML-файлу с графиком и всех данных
generated_html_file = None
data = None

# Глобальная переменная для хранения моделей МО
model_01 = None
model_02 = None
model_03 = None
model_04 = None


def generate_data_and_plot():
    global generated_html_file
    global data

    # Получаем данные ИПЦ
    df = fn.get_CPI_data_from_rosstat(type_CPI='01').merge(
        fn.get_CPI_data_from_rosstat(type_CPI='02')[['Дата', fn.CPI_guide['02'][0]]],
        on='Дата',
        how='left').merge(fn.get_CPI_data_from_rosstat(type_CPI='03')[['Дата', fn.CPI_guide['03'][0]]],
                          on='Дата',
                          how='left').merge(fn.get_CPI_data_from_rosstat(type_CPI='04')[['Дата', fn.CPI_guide['04'][0]]],
                                            on='Дата',
                                            how='left')

    df['Дата'] = pd.to_datetime(df['Дата'])

    # Визуализируем исходные данные ИПЦ
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=df['Дата'][9 * 12:],
                             y=df[fn.CPI_guide['01'][0]][9 * 12:],
                             name=fn.CPI_guide['01'][0],
                             marker=dict(color='#0088BB')))
    fig.add_trace(go.Scatter(x=df['Дата'][9 * 12:],
                             y=df[fn.CPI_guide['02'][0]][9 * 12:],
                             name=fn.CPI_guide['02'][0],
                             marker=dict(color='#EE1133')))
    fig.add_trace(go.Scatter(x=df['Дата'][9 * 12:],
                             y=df[fn.CPI_guide['03'][0]][9 * 12:],
                             name=fn.CPI_guide['03'][0],
                             marker=dict(color='#FFBB44')))
    fig.add_trace(go.Scatter(x=df['Дата'][9 * 12:],
                             y=df[fn.CPI_guide['04'][0]][9 * 12:],
                             name=fn.CPI_guide['04'][0],
                             marker=dict(color='#555555')))

    fig.update_layout(legend_orientation="h", legend=dict(x=.5, xanchor="center"), margin=dict(l=30, r=30, t=20, b=30))
    fig.update_traces(hoverinfo="all", hovertemplate="Месяц: %{x}<br>Значение: %{y}")

    # Добавляем кнопки для отображения конкретных периодов времени и слайдер
    fig.update_layout(
        xaxis=dict(rangeselector=dict(buttons=list([dict(count=1, label="1 год", step="year", stepmode="backward"),
                                                    dict(count=2, label="2 года", step="year", stepmode="backward"),
                                                    dict(count=5, label="5 лет", step="year", stepmode="backward"),
                                                    dict(count=10, label="10 лет", step="year", stepmode="backward"),
                                                    dict(count=20, label="20 лет", step="year", stepmode="backward")])),
                   rangeslider=dict(visible=True), type="date"))

    # Сохраняем интерактивный график в формате HTML
    fig.write_html("./static/plotly_graph.html")
    generated_html_file = "./static/plotly_graph.html"

    df2 = fn.get_DollarER_data_from_cbr()
    df2['Дата'] = pd.to_datetime(df2['Дата'])

    df3 = fn.get_KR_data_from_cbr()
    df3['Дата'] = pd.to_datetime(df3['Дата'])

    df_glob = df.merge(df2, on='Дата', how='left').merge(df3, on='Дата', how='left')

    data = df_glob.dropna()

    data['Год'] = pd.DatetimeIndex(data['Дата']).year
    data['Месяц'] = pd.DatetimeIndex(data['Дата']).month


def plot_forecast(model, X_val: np.ndarray, y_val: np.ndarray, type_CPI: str):
    global data
    prediction = model.predict(X_val)

    std_error = np.sqrt(mean_squared_error(y_val, prediction))

    lower_bound = (prediction - 1.96 * std_error).ravel()
    upper_bound = (prediction + 1.96 * std_error).ravel()

    fig = make_subplots(rows=1, cols=1)

    # Исходные данные и прогноз
    fig.add_trace(go.Scatter(x=data['Дата'][-36:],
                             y=data[fn.CPI_guide[type_CPI][0]][-36:],
                             mode='lines',
                             name=fn.CPI_guide[type_CPI][0],
                             marker=dict(color=fn.CPI_guide[type_CPI][1])))
    fig.add_trace(go.Scatter(x=data['Дата'][-6:],
                             y=pd.Series(prediction.flatten()),
                             mode='lines',
                             name='Прогноз',
                             marker=dict(color='#00b050'),
                             line=dict(dash='dash')))

    # Нижний и верхний доверительные интервалы
    fig.add_trace(go.Scatter(x=data['Дата'][-6:],
                             y=lower_bound,
                             fill=None, mode='lines',
                             name='Верхний дов. интервал 95%',
                             marker=dict(color='#92d050')))
    fig.add_trace(go.Scatter(x=data['Дата'][-6:],
                             y=upper_bound,
                             fill='tonexty',
                             mode='lines',
                             name='Нижний дов. интервал 95%',
                             marker=dict(color='#92d050'),
                             fillcolor='rgba(146, 208, 80, 0.2)'))

    fig.update_layout(legend_orientation='h',
                      legend=dict(x=.5, xanchor='center'),
                      margin=dict(l=30, r=30, t=20, b=30))
    fig.update_traces(hoverinfo='all',
                      hovertemplate='Месяц: %{x}<br>Значение: %{y}')

    fig.write_html(f'./static/{type_CPI}_graph.html')


@app.route('/')
def main() -> str:
    global generated_html_file
    # Если график еще не сгенерирован, генерируем его
    if not generated_html_file:
        generate_data_and_plot()
    return render_template('main.html', path=request.path)


@app.route('/forecast')
def forecast() -> str:
    global data
    global model_01
    global model_02
    global model_03
    global model_04

    # Экзогенные ряды для всех моделей получились идентичными
    X_val = data[-6:].loc[:, ['Курс Доллара_MoM', 'Ставка']].values

    if not model_01:
        model_01 = fn.load_model(type_CPI='01')
        plot_forecast(model=model_01,
                      X_val=X_val,
                      y_val=data[-6:].loc[:, [fn.CPI_guide['01'][0]]].values,
                      type_CPI='01')
    if not model_02:
        model_02 = fn.load_model(type_CPI='02')
        plot_forecast(model=model_02,
                      X_val=X_val,
                      y_val=data[-6:].loc[:, [fn.CPI_guide['02'][0]]].values,
                      type_CPI='02')
    if not model_03:
        model_03 = fn.load_model(type_CPI='03')
        plot_forecast(model=model_03,
                      X_val=X_val,
                      y_val=data[-6:].loc[:, [fn.CPI_guide['03'][0]]].values,
                      type_CPI='03')
    if not model_04:
        model_04 = fn.load_model(type_CPI='04')
        plot_forecast(model=model_04,
                      X_val=X_val,
                      y_val=data[-6:].loc[:, [fn.CPI_guide['04'][0]]].values,
                      type_CPI='04')

    return render_template('forecast.html', path=request.path)


if __name__ == '__main__':
    app.run(debug=False)
