from lxml import html
import requests

url = 'http://old.duma.gov.ru/structure/deputies/?letter=%D0%92%D1%81%D0%B5'
htmlResult = requests.get(url)
tree = html.fromstring(htmlResult.text.encode('utf8'))
deputyTr = tree.xpath('//table[@id="lists_list_elements_35"]')[0].xpath('tr')

with open('deputies.txt', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
    for i in range(1, len(deputyTr)):
        deputyTd = deputyTr[i].xpath('td')
        deputyName = deputyTd[1].xpath('a')[0].text
        deputyParty = deputyTd[2].xpath('a')[0].text
        deputyUrl = 'http://old.duma.gov.ru' + deputyTd[1].xpath('a')[0].get('href')
        job = deputyTd[3].text_content()
        file.write(';'.join([deputyName, deputyParty, job, deputyUrl]) + '\n')

