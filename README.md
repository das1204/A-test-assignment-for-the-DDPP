# Тестовое задание для ДДПП
Программное решение, которое:
* Автоматически загружает данные по индексам потребительских цен (ИПЦ) с официального [сайта Росстата](https://rosstat.gov.ru/statistics/price#),
* Визуализирует полученные данные,
* Использует 4 модели МО для прогноза на 6 месяцев и визуализирует результаты в виде интерактивных графиков на веб-сайте.

Весь код упакован в Docker-контейнер и размещен на GitHub.
<!-- описание репозитория -->

<!--Блок информации о репозитории в бейджах-->

<!--Установка-->
## Установка
У вас должны быть установлены [зависимости проекта](https://github.com/das1204/A-test-assignment-for-the-DPPD#зависимости)

1. Клонирование репозитория 

```git clone https://github.com/das1204/A-test-assignment-for-the-DPPD.git```

2. Переход в директорию Oxygen

```cd A-test-assignment-for-the-DPPD```

3. Установка зависимостей

```pip3 install -r requirements.txt```

4. Запуск скрипта для демонстрации работы

```python3 app.py```


<!--зависимости-->
## Зависимости
Эта программа зависит от интепретатора Python версии 3.9 или выше.

<!--Логика работы-->
## Алгоритм

### Главная страница

При запуске скрипта ```app.py``` автоматически открывается главная страница проекта (```/```).
P.S. Первый запуск при каждом новом открытии сайта занимает какое-то время, поскольку автоматически подгружаются данные ИПЦ с Росстата, а также [Ключевая ставка](https://cbr.ru/hd_base/KeyRate/?UniDbQuery.Posted=True) и [Курс Доллара США](https://cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so=0&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ=R01235) с сайта Банка России.

![main_web](./img/main_web.png)

Основным элементом главной страницы сайта является интегрированный интерактивный график созданный с помощью библиотеки ```Plotly```.
На график выводяться все четыря ряда ИПЦ за XXI век:
* ![#0088BB](https://placehold.co/15x15/0088BB/0088BB.png) ИПЦ на товары и услуги 
* ![#EE1133](https://placehold.co/15x15/EE1133/EE1133.png) ИПЦ на продовольственные товары 
* ![#FFBB44](https://placehold.co/15x15/FFBB44/FFBB44.png) ИПЦ на непродовольственные товары 
* ![#74777B](https://placehold.co/15x15/74777B/74777B.png) ИПЦ на услуги

Кроме того, на график добавлены 5 кнопок для выбора отображаемого временного периода (1, 2, 5, 10 и 20 лет), а также селектор, позволяющий выбирать произвольный отображаемый диапазон.

Подписи рядов также являются интерактивными: нажание на название ряда скрывает/отображает его на графике.

### Страница с прогнозом

При первом переходе на старницу "Прогноз ИПЦ" (```/forecast```) автоматически подгружаются 4 модели МО, обученные специально для каждого из рядов и строиться прогноз на 6 точек.

Для каждого из ![#00b050](https://placehold.co/15x15/00b050/00b050.png) рядов прогноза строиться ![#92d050](https://placehold.co/15x15/92d050/92d050.png) верхний и нижний доверительный интервал на уровне 95%.

Формула для нахождения значений верхней и нижней границ:

$$x_{ui} = x_i + 1.96 * RMSE$$

$$x_{li} = x_i - 1.96 * RMSE$$

![main_web](./img/forecast_web.png)

Все графики, как и график на главной странице являются интерактивнями.

### Выбор модели МО

Для каждого из рядов ИПЦ подбиралась уникальная модель МО из списка:
* ``````



