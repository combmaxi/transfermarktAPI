from fastapi import FastAPI
import random
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import math
from multichat.asgi import application
#python -m uvicorn main:app --reload

app = FastAPI()
@app.get("/")
def accueil():
    return {"Message": "Bienvenue dans l'API de scraping TRANSFERMARKT"}


@app.get("/searchPlayer/{language}_{name}")
def generer_nombre(language: str, name: str):
    """
    Cette fonction donne le résultat de recherche sur la première page en fonction du nom du joueur renseigné et du sexe du joueur.
    """ 
    #Correction des exceptions UK, Brazil,...
    language = language.lower()
    if(language != 'fr'):
        
        match language:
            case 'uk':
                language = 'co.uk'
            case 'br':
                language = 'com.br'
            case 'ar':
                language = 'com.ar'
            case 'in':
                language = 'co.in'
            case 'id':
                language = 'co.id'
            case 'kr':
                language = 'co.kr'
            case 'za':
                language = 'co.za'
            case 'tr':
                language = 'com.tr'

    domain = 'https://www.transfermarkt.' + language + '/'       
    url = domain + 'schnellsuche/ergebnis/schnellsuche?query=' + name.lower()

    userAgent = random.randint(5,5999)
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)

    playersLists = []
    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        bigRowsWithLinesList = soup.findAll('div', {'class' : 'large-12 columns'})
        #Envoi d'aucun joueur si la recherche n'aboutit à rien en fonction de l'entête du tableau
        tableTitle = bigRowsWithLinesList[0].find('h2', {'class' : 'content-box-headline'}).text
        match language:
            case 'fr':
                if " joueurs" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'co.uk' | 'us' | 'co.in' | 'co.kr'|'co.za' | 'com':
                if " players" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'es' | 'com.ar' | 'co' | 'mx' | 'pe':
                if " jugador" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'de' | 'at' | 'ch':
                if " spielern" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'it':
                if " giocatori" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'ro':
                if " jucători" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'gr':
                if "παικτών" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'com.br' | 'pt':
                if " jogador" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'co.id':
                if " pemain" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'com.tr':
                if " oyunculara" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'be' | 'nl':
                if " spelers " not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'pl':
                if "Wyniki wyszukiwania" not in tableTitle: 
                    return { 'players' : 'No players found' }
            case 'jp':
                if "選手検索結果" not in tableTitle: 
                    return { 'players' : 'No players found' }
        oddLines = bigRowsWithLinesList[0].findAll('tr', {'class' : 'odd'})
        evenLines = bigRowsWithLinesList[0].findAll('tr', {'class' : 'even'})
        #Calcul de nombre de ligne à analyser sachant que les index sont alternés
        nbLines = len(oddLines) + len(evenLines)
        rangeLines = math.trunc(nbLines/2)
        oddNumber = False
        if nbLines % 2 == 1:
            rangeLines += 1
            oddNumber = True
        for index in range(rangeLines):
            print(str(index) + ' ' + str(rangeLines))
            #Alternance entre la ligne de class Odd et celle de classe Even
            for oddOrEven in range(2):
                if oddOrEven == 0 :
                    lines = oddLines
                else:
                    if (oddNumber == True) and (index == rangeLines - 1):
                        break
                    else: 
                        lines = evenLines
                linkOnGoing = lines[index].find('td', {'class' : 'hauptlink'}).find('a')['href']
                #Séparation du nom et du prénom
                fullName = lines[index].find('td', {'class' : 'hauptlink'}).text
                listName = fullName.split(" ")
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Savoir si joueur à la retraite en fonction de l'image du club
                if tdList[5].find('img')['src'] == "https://tmssl.akamaized.net/images/wappen/tiny/123.png?lm=1456997286":
                    careerEnded = True
                else:
                    careerEnded = False
                #Séparation des nationalités dans une liste
                citizenshipList =[]
                imgCitizenshipList = tdList[7].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
                #Définition du club ou null si retraité
                if careerEnded == 1 :
                    club = None
                else:
                    club = tdList[5].find('img')['title']
                #Création du json joueur
                playersLists.append({
                    'transferMarktId' : linkOnGoing.split('/')[4],
                    'url' : domain + linkOnGoing,
                    'name' : listName[len(listName)-1],
                    'fullName' : fullName,
                    'imageURL' : lines[index].find('img')['src'],  
                    'age' : tdList[6].text,  
                    'citizenship' : citizenshipList,
                    'isRetired' : careerEnded,
                    'position' : tdList[4].text,
                    'club' : club,
                    'marketValue' : tdList[8].text,
                    'agent' :  tdList[9].text
                })
            
        playerOnGoingJson = { 'players' : playersLists }
        return playerOnGoingJson
                

@app.get("/searchClub/{language}_{name}")
def searchClub(language: str, name: str):
    """
    Cette fonction donne le résultat de recherche sur la première page en fonction du nom du joueur renseigné et du sexe du joueur.
    """ 
    #Correction des exceptions UK, Brazil,...
    language = language.lower()
    if(language != 'fr'):
        
        match language:
            case 'uk':
                language = 'co.uk'
            case 'br':
                language = 'com.br'
            case 'ar':
                language = 'com.ar'
            case 'in':
                language = 'co.in'
            case 'id':
                language = 'co.id'
            case 'kr':
                language = 'co.kr'
            case 'za':
                language = 'co.za'
            case 'tr':
                language = 'com.tr'

    domain = 'https://www.transfermarkt.' + language + '/'       
    url = domain + 'schnellsuche/ergebnis/schnellsuche?query=' + name.lower()

    userAgent = random.randint(5,5999)
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)

    playersLists = []
    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        bigRowsWithLinesList = soup.findAll('div', {'class' : 'large-12 columns'})
        #Envoi d'aucun joueur si la recherche n'aboutit à rien en fonction de l'entête du tableau
        clubsTableIndex = 
        nbOfTables = len(bigRowsWithLinesList)
        for index in range(nbOfTables):
            tableTitle = bigRowsWithLinesList[index].find('h2', {'class' : 'content-box-headline'}).text
            match language:
                case 'fr':
                    if "Résultats de recherche: clubs" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'co.uk' | 'us' | 'co.in' | 'co.kr'|'co.za' | 'com':
                    if "Search results: Clubs" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'es' | 'com.ar' | 'co' | 'mx' | 'pe':
                    if "Buscar resultados: Clubes" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'de' | 'at' | 'ch':
                    if "Suchergebnisse zu Vereinen" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'it':
                    if "Risultati società" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'ro':
                    if "Rezultatele căutării: Cluburi" not in tableTitle: 
                        if index == nbOfTables - 1 :
                        return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'gr':
                    if "Αποτελέσματα αναζήτησης ομάδων" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'com.br' | 'pt':
                    if "Resultados da pesquisa para Clubes" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'co.id':
                    if "Hasil pencarian: Klub" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'com.tr':
                    if "Arama sonuçları: Kulüpler" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'be' | 'nl':
                    if "Clubs" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'pl':
                    if "Lista drużyn" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
                case 'jp':
                    if "検索結果: クラブ" not in tableTitle: 
                        if index == nbOfTables - 1 :
                            return { 'clubs' : 'No clubs found' }
                    else :
                        clubsTableIndex = index
                        break
        oddLines = bigRowsWithLinesList[clubsTableIndex].findAll('tr', {'class' : 'odd'})
        evenLines = bigRowsWithLinesList[clubsTableIndex].findAll('tr', {'class' : 'even'})
        #Calcul de nombre de ligne à analyser sachant que les index sont alternés
        nbLines = len(oddLines) + len(evenLines)
        rangeLines = math.trunc(nbLines/2)
        oddNumber = False
        if nbLines % 2 == 1:
            rangeLines += 1
            oddNumber = True
        for index in range(rangeLines):
            print(str(index) + ' ' + str(rangeLines))
            #Alternance entre la ligne de class Odd et celle de classe Even
            for oddOrEven in range(2):
                if oddOrEven == 0 :
                    lines = oddLines
                else:
                    if (oddNumber == True) and (index == rangeLines - 1):
                        break
                    else: 
                        lines = evenLines
                linkOnGoing = lines[index].find('td', {'class' : 'hauptlink'}).find('a')['href']
                #Séparation du nom et du prénom
                fullName = lines[index].find('td', {'class' : 'hauptlink'}).text
                listName = fullName.split(" ")
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Savoir si joueur à la retraite en fonction de l'image du club
                if tdList[5].find('img')['src'] == "https://tmssl.akamaized.net/images/wappen/tiny/123.png?lm=1456997286":
                    careerEnded = True
                else:
                    careerEnded = False
                #Séparation des nationalités dans une liste
                citizenshipList =[]
                imgCitizenshipList = tdList[7].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
                #Définition du club ou null si retraité
                if careerEnded == 1 :
                    club = None
                else:
                    club = tdList[5].find('img')['title']
                #Création du json joueur
                playersLists.append({
                    'transferMarktId' : linkOnGoing.split('/')[4],
                    'url' : domain + linkOnGoing,
                    'name' : listName[len(listName)-1],
                    'fullName' : fullName,
                    'imageURL' : lines[index].find('img')['src'],  
                    'age' : tdList[6].text,  
                    'citizenship' : citizenshipList,
                    'isRetired' : careerEnded,
                    'position' : tdList[4].text,
                    'club' : club,
                    'marketValue' : tdList[8].text,
                    'agent' :  tdList[9].text
                })
            
        playerOnGoingJson = { 'players' : playersLists }
        return playerOnGoingJson
                



@app.get("/giveCaracteristicsWithName/{brand}_{name}")
def generer_nombre(brand: str, name: str):
    """
    Cette fonction donne les caractéristiques d'un appareil en fonction du nom officiel.
    """

    reelName = name.replace(" ","").lower()
    nameWithoutBrand = reelName[len(brand):len(reelName)]
    url = 'https://www.gsmchoice.com/en/catalogue/'+ brand.lower() +'/' + nameWithoutBrand
    
    print(url)
    response = requests.get(url)

    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        titles = soup.find('th', {'class' : 'phoneCategoryName'})
        values = soup.find('td', {'class' : 'phoneCategoryValue'})
        return {"GSMName" : values.text.replace('\n','')}
        for index, item in enumerate(items):
            print(str(item.text))
            if name in item.text: 
                result = item.text
                return {"GSMName" : result}

class NombreHasard (BaseModel):
    taille_homme: float
    taille_femme: float

@app.post("/test_post/")
def generer_taille_fils(datass: NombreHasard):
    """
    Bonjour DESCRIPTION
    """
    return {"taille_filsss": datass.taille_femme + datass.taille_homme}