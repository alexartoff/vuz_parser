## Парсер даных ВУЗов (УрФУ и СПбГУ)
1. установить requests, BeautifulSoup, fake_useragent
2. откорректировать константы URFU_USER_ID и SPBGU_USER_ID - ввести СНИЛС человека
3. указать нужный код специальности в УрФУ, на которую поступает человек
4. выбрать входящие в состав УрФУ институты, по которым будет осуществлён поиск
5. указать ID (код) специальностей в СПбГУ, по которым будет осуществлён поиск
6. запустить 'python3 main.py'

По результатам будут загружены актуальные списки, выполнен поиск по СНИЛСам по указанным институтам (УрФУ) и специальностям (СПбГУ), сформированы CSV-файлы, отсортированные по порядку прохождения на бюджетные места.
ВНИМАНИЕ! расчеты приблизительные, с учетом расставленных поступающими приоритетов. "Уходящие" на другие специальности абитуриенты, в итоговые CSV-файлы не попадают, информация о них печатается в терминале
