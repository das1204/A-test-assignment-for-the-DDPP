# Импорт стандартных библиотек
from datetime import date
from io import BytesIO
import pickle
import warnings

# Импорт библиотек для работы с данными и парсинга
import pandas as pd
import plotly.io as pio
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Устанавливаем стандартную тему Plotly
pio.templates.default = 'plotly'

warnings.filterwarnings('ignore')


def load_model(type_CPI: str):
    if type_CPI == '01':
        file_path = './models/01.pkl'
    elif type_CPI == '02':
        file_path = './models/02.pkl'
    elif type_CPI == '03':
        file_path = './models/03.pkl'
    elif type_CPI == '04':
        file_path = './models/04.pkl'
    with open(file_path, 'rb') as model_file:
        return pickle.load(model_file)


months = {'январь': '01',
          'февраль': '02',
          'март': '03',
          'апрель': '04',
          'май': '05',
          'июнь': '06',
          'июль': '07',
          'август': '08',
          'сентябрь': '09',
          'октябрь': '10',
          'ноябрь': '11',
          'декабрь': '12'}

CPI_guide = {'01': ['ИПЦ на товары и услуги', '#0088BB'],
             '02': ['ИПЦ на продовольственные товары', '#EE1133'],
             '03': ['ИПЦ на непродовольственные товары', '#FFBB44'],
             '04': ['ИПЦ на услуги', '#74777B']}


def get_CPI_data_from_rosstat(type_CPI: str) -> pd.DataFrame:
    start_url = 'https://rosstat.gov.ru'
    try:
        # Отправляем GET-запрос к исходному URL
        response = requests.get(url=f'{start_url}/statistics/price#',
                                headers={'User-Agent': str(UserAgent().random).strip()})
        # Использую str() и strip() т.к. встречаются UserAgent с начальными/конечными пробелами, ведущие к ошибке

        # Создаем объект BeautifulSoup для парсинга HTML-кода страницы
        soup = BeautifulSoup(response.content, 'lxml')

        # Перебираем каждый элемент внутри контейнера
        for mini_soup in soup.find(name='div', class_='document-list__items').find_all(name='div',
                                                                                       class_='document-list__item document-list__item--row'):
            if 'Индексы потребительских цен на товары и услуги по Российской Федерации, месяцы' in mini_soup.find(
                    name='div', class_='document-list__item-title').text:
                # Получаем часть URL для загрузки файла с данными
                file_url = mini_soup.find(name='div', class_='document-list__item-link').find(name='a',
                                                                                              class_='btn btn-icon btn-white btn-br btn-sm').get(
                    'href')
    except requests.exceptions.RequestException as e:
        print(f'Произошла ошибка при выполнении запроса: {e}')

    df = pd.read_excel(f'{start_url}{file_url}', sheet_name=type_CPI)

    # Удаляем строки, ненужные для формирования последующего временного ряда
    df = df.drop(index=[0, 1, 3, 16, 17, 18, 19, 20])
    df.iloc[0, 0] = 1
    df.columns = df.iloc[0]
    df = df.drop(index=2).reset_index(drop=True)

    # Формируем столбец заголовка
    df.columns = df.columns.astype(int)
    df = df.rename_axis(columns=None)
    df = df.rename(columns={1: 'Дата'})

    # Добавляем нули для однозначных чисел в месяцах (1 -> 01)
    for month in months:
        df['Дата'] = df['Дата'].replace(month, months[month])

    # Преобразуем DataFrame во временной ряд
    df = df.melt(id_vars=['Дата'], var_name='Год', value_name=CPI_guide[type_CPI][0])

    # Формируем нового столбца с датами
    df[['Дата', 'Год']] = df[['Дата', 'Год']].astype(str)
    df['Дата'] = pd.to_datetime(df['Дата'] + '.' + df['Год'], format='%m.%Y')
    df = df.sort_values('Дата')
    df = df.dropna()

    # Удаляем столбец с годами
    df = df.drop(columns=['Год'])

    return df


def get_DollarER_data_from_cbr() -> pd.DataFrame:
    response = requests.get(
        f'https://cbr.ru/Queries/UniDbQuery/DownloadExcel/98956?Posted=True&so=1&mode=1&VAL_NM_RQ=R01235&From=01.07'
        f'.1992&To={date.today().day}.{date.today().month}.{date.today().year}&FromDate=07%2F01%2F1992&ToDate='
        f'{date.today().day}%2F{date.today().month}%2F{date.today().year}',
        headers={'User-Agent': str(UserAgent().random).strip()})

    df = pd.read_excel(BytesIO(response.content))

    df.drop(['nominal', 'cdx'], axis=1, inplace=True)
    df.columns = ['Дата', 'Курс Доллара']
    df['Дата'] = pd.to_datetime(df['Дата'], format='%Y-%m-%d')
    df = df.astype({'Курс Доллара': float})
    df = df.sort_values(by=['Дата'])

    df = df.groupby(pd.PeriodIndex(df['Дата'], freq='M'))['Курс Доллара'].mean().reset_index()
    df['Дата'] = df['Дата'].dt.to_timestamp()

    df['Курс Доллара_MoM'] = df['Курс Доллара'].pct_change()
    df['Курс Доллара_MoM'] *= 100

    return df


def get_KR_data_from_cbr() -> pd.DataFrame:
    response = requests.get(
        f'https://cbr.ru/hd_base/KeyRate/?UniDbQuery.Posted=True&UniDbQuery.From=17.09.2013&UniDbQuery.To={date.today().day}.{date.today().month}.{date.today().year}',
        headers={'User-Agent': str(UserAgent().random).strip()})
    soup = BeautifulSoup(response.content, 'lxml')

    table = soup.find(name='table', class_='data')

    df = pd.DataFrame(
        columns=[table.find_all('tr')[0].find_all('th')[0].text, table.find_all('tr')[0].find_all('th')[1].text])

    dates = []
    values = []

    for i in range(len(table.find_all('tr')))[1:]:
        dates.append(table.find_all('tr')[i].find_all('td')[0].text)
        values.append(table.find_all('tr')[i].find_all('td')[1].text)

    df[table.find_all('tr')[0].find_all('th')[0].text] = dates
    df[table.find_all('tr')[0].find_all('th')[1].text] = values

    df['Дата'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y')
    df[table.find_all('tr')[0].find_all('th')[1].text] = df[table.find_all('tr')[0].find_all('th')[1].text].str.replace(
        ',', '.').astype(float)
    df = df.sort_values(by=['Дата'])

    df = df.groupby(pd.PeriodIndex(df['Дата'], freq='M'))[
        table.find_all('tr')[0].find_all('th')[1].text].mean().reset_index()
    df['Дата'] = df['Дата'].dt.to_timestamp()

    return df

