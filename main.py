# -*- coding: utf-8 -*-
from lxml import html
import requests
import json
import util

deputFile = open('deputies.txt', mode='r',encoding= 'utf8', buffering=1)
logFile = open('log.txt', mode='w', encoding='utf8', buffering=1)
deputLines = deputFile.readlines()
deputFile.close()

problemDeputs = 0
validDeclarations = []
invalidDeclarations = []

for i in deputLines:
    try:
        valid = True
        deputProps = i.rstrip().split(';')
        url = deputProps[3]
        htmlResult = requests.get(url)
        tree = html.fromstring(htmlResult.text.encode('utf8'))
        table = tree.xpath('//div[@class="round-block rb-no-top-corn tab-2-box"]')[0]
        parts = table.xpath('//div[@class="c-tab-2"]')
        paramSearch = table.xpath('//ul[@class="param-search"]')
        haveOwnEstate = util.haveOwnEstate(paramSearch[1])
        haveUseEstate = util.haveUseEstate(paramSearch[1])

        firstPart = parts[0]
        if len(parts) > 1:
            secondPart = parts[1]
        else:
            secondPart = None

        deputStruct = {}

        #Имя
        deputFullName = firstPart.xpath('//tr')[1].xpath('//td')[0].text
        nameParts = deputFullName.split()
        deputStruct["person"] = {
            "name": deputFullName,
            "family_name": nameParts[0],
            "given_name": nameParts[1],
            "patronymic_name": nameParts[2],
            "role": util.getRole(deputProps[2])
        }

        deputStruct["office"] = {
            "name": "Государственная Дума",
            "url": "http://www.duma.gov.ru/",
            "type": "Федеральный, без региональной структуры",
            "region": "null"
        }

        deputStruct["party"] = util.getParty(deputProps[1])

        deputStruct["year"] = 2017

        #Документ
        deputStruct["document"] = {
            "type": "Антикоррупционная декларация",
            "name": "Сведения о доходах, имуществе и обязательствах имущественного характера депутата и членов его семьи за период с 01.01.2017 по 31.12.2017",
            "url": deputProps[3]
        }

        #Доход
        deputStruct["incomes"] = []
        incomesTr = firstPart.xpath('//table[@class="data-2 data-2-has-even"]')[0].xpath('tr')
        for i in range(1, len(incomesTr)):
            incomesTd = incomesTr[i].xpath('td')

            #Размер
            size = util.getIncomeSize(incomesTd[1].text)

            #Владелец
            relative = util.getRelative(incomesTd[0].text, deputStruct["person"]["name"])

            if size != 0.0:
                deputStruct["incomes"].append({
                    "size": size,
                    "relative": relative
                })

        deputStruct["real_estates"] = []

        #Недвижимость в собственности
        if (haveOwnEstate):
            estatesTr = firstPart.xpath('//table[@class="data-2 data-2-has-even"]')[1].xpath('tr')
            curOwner = ''
            for i in range(1, len(estatesTr)):
                try:
                    estatesTd = estatesTr[i].xpath('td')

                    #Комментарий
                    comment = ''


                    #Владелец
                    owner = estatesTd[0].text
                    if estatesTd[1].text == None:
                        continue
                    owner = util.getOwner(owner, curOwner)
                    curOwner = owner
                    relative = util.getRelative(owner, deputStruct["person"]["name"])


                    #Тип
                    rawType = estatesTd[1].text
                    type = util.getEstateType(rawType)

                    #Площадь
                    rawSquare = estatesTd[2].text
                    square = util.getSquare(estatesTd[2].text)

                    #Регион
                    country = estatesTd[3].text

                    #Право собственности
                    own_type = util.getOwnType(rawType, 'В собственности')

                    comment = util.getEstateComment([estatesTd[1].text, estatesTd[2].text, estatesTd[3].text])
                    share = estatesTd[1].text
                    if share.find("долевая") != -1:
                        shareType = "Долевая собственность"

                        amount = util.getAmountShare(share)
                        if amount is None:
                            comment = util.addComment(comment, 'Долевая собственность: ' + share)
                            amount = "null"

                        share_amount = int(amount[0]) / int(amount[1])
                        share_amount = util.getRoundEstateSize(share_amount)
                    elif share.lower().find('совместная собственность') != -1:
                        shareType = "Совместная собственность"
                        share_amount = "null"
                    else:
                        shareType = "Индивидуальная"
                        share_amount = "null"

                    deputStruct["real_estates"].append({
                        "name": rawType,
                        "type": type,
                        "square": square,
                        "country": country,
                        "region": "null",
                        "comment": comment,
                        "own_type": own_type,
                        "share_type": shareType,
                        "share_amount": share_amount,
                        "relative": relative
                    })
                except Exception as e:
                    util.writeLog([e,deputProps[0],deputProps[3]], logFile)
                    valid = False
        if (haveUseEstate):
            #Недвижимость в пользовании
            if (haveOwnEstate):
                tableId = 2
            else:
                tableId = 1
            estatesTr = firstPart.xpath('//table[@class="data-2 data-2-has-even"]')[tableId].xpath('tr')
            curOwner = ''
            for i in range(1, len(estatesTr)):
                try:
                    estatesTd = estatesTr[i].xpath('td')

                    #Комментарий
                    comment = ''
                    #Владелец
                    owner = estatesTd[0].text
                    if estatesTd[1].text == None:
                        continue
                    owner = util.getOwner(owner, curOwner)
                    curOwner = owner
                    relative = util.getRelative(owner, deputStruct["person"]["name"])

                    #Тип
                    rawType = estatesTd[1].text
                    type = util.getEstateType(rawType)

                    #Площадь
                    rawSquare = estatesTd[2].text
                    square = util.getSquare(estatesTd[2].text)


                    #Регион
                    country = estatesTd[3].text

                    #Право собственности
                    own_type = util.getOwnType(rawType,'В пользовании')

                    comment = util.getEstateComment([estatesTd[1].text, estatesTd[2].text, estatesTd[3].text])
                    share = estatesTd[1].text
                    if share.find("долевая") != -1:
                        shareType = "Долевая собственность"
                    elif share.lower().find('совместная собственность') != -1:
                        shareType = "Совместная собственность"
                    else:
                        shareType = "Индивидуальная"
                    share_amount = "null"

                    deputStruct["real_estates"].append({
                        "name": rawType,
                        "type": type,
                        "square": square,
                        "country": country,
                        "region": "null",
                        "comment": comment,
                        "own_type": own_type,
                        "share_type": shareType,
                        "share_amount": share_amount,
                        "relative": relative
                    })
                except Exception as e:
                    util.writeLog([e, deputProps[0], deputProps[3]], logFile)
                    valid = False

        if secondPart != None:
            #Транспортные средства
            deputStruct["vehicles"] = []
            vehiclesTr = secondPart.xpath('div[@class="inner-data-2"]')[0].xpath('table[@class="data-2 data-2-has-even"]')[0].xpath('tr')
            curOwner = ''
            for i in range(1, len(vehiclesTr)):
                vehiclesTd = vehiclesTr[i].xpath('td')

                #Владелец
                owner = util.getOwner(vehiclesTd[0].text, curOwner)
                curOwner = owner
                relative = util.getRelative(owner, deputStruct["person"]["name"])

                #Название
                full_name = vehiclesTd[2].text

                #Тип
                type = util.carType(vehiclesTd[1].text.title(), full_name)

                deputStruct["vehicles"].append({
                    "full_name": full_name,
                    "type": type,
                    "brand": "null",
                    "manufacture_year": "null",
                    "relative": relative
                })
        if valid:
            validDeclarations.append(deputStruct)
        else:
            invalidDeclarations.append(deputStruct)
    except Exception as e:
        print(e, deputProps[0], deputProps[3])

with open('validDeputies.json', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
    validJson = json.dumps(validDeclarations, ensure_ascii=False)
    validJson = util.replaceNullQuotes(validJson)
    file.write(validJson)

with open('invalidDeputies.json', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
    invalidJson = json.dumps(invalidDeclarations, ensure_ascii=False)
    invalidJson = util.replaceNullQuotes(invalidJson)
    file.write(invalidJson)

print('Валидных деклараций -', len(validDeclarations))
print('Невалидных деклараций -', len(invalidDeclarations))
