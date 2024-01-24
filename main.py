from fastapi import FastAPI
import random
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import math
#from multichat.asgi import application
#python -m uvicorn main:app --reload

def correctDomainExtension(domain: str):
    domain = domain.lower()
    if(domain != 'fr'):        
        match domain:
            case 'uk':
                domain = 'co.uk'
            case 'br':
                domain = 'com.br'
            case 'ar':
                domain = 'com.ar'
            case 'in':
                domain = 'co.in'
            case 'id':
                domain = 'co.id'
            case 'kr':
                domain = 'co.kr'
            case 'za':
                domain = 'co.za'
            case 'tr':
                domain = 'com.tr'
    return domain

app = FastAPI()
@app.get("/")
def accueil():
    return {"Message": "Bienvenue dans l'API de scraping TRANSFERMARKT"}


@app.get("/searchPlayer/{language}_{name}")
def generer_nombre(language: str, name: str):
    """
    Cette fonction donne le résultat de recherche des joueurs masculins existants sur TransfertMarkt sur la première page en fonction de la langue et du nom du joueur renseignés. La langue doit être les 2 lettres de l'extension de domaine associée, et l'ID doit être sous forme numérique.
    """ 
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language     
    url = domain + '/schnellsuche/ergebnis/schnellsuche?query=' + name.lower()
    #Camouflage de l'API
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
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
   Cette fonction donne le résultat de recherche des clubs existants sur TransfertMarkt sur la première page en fonction de la langue et du nom du club renseignés. La langue doit être les 2 lettres de l'extension de domaine associée.
    """ 
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language      
    url = domain + '/schnellsuche/ergebnis/schnellsuche?query=' + name.lower()
    #Brouillage des requêtes
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)
    clubsList = []    
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        #Nombre de tableaux principaux
        bigRowsWithLinesList = soup.findAll('div', {'class' : 'large-12 columns'})
        #Envoi d'aucun joueur si la recherche n'aboutit à rien en fonction de l'entête du tableau
        clubsTableIndex = 0
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
                #Liste des TD dont les valeurs de texte correspondent ensuite à chaque case
                tdList = lines[index].findAll('td')
                #Création du json joueur
                clubsList.append({
                    'transferMarktId' : linkOnGoing.split('/')[4],
                    'url' : domain + linkOnGoing,
                    'imageURL' : lines[index].find('img')['src'],
                    'name' : lines[index].find('td', {'class' : 'hauptlink'}).text,
                    'leagueName' : tdList[3].text,
                    'country' : tdList[4].find('img')['title'],
                    'staff' : tdList[5].text,
                    'marketValue' : tdList[6].text,
                    'stadiumName' : tdList[8].find('a')['title']
                })            
        return { 'clubs' : clubsList }
                

@app.get("/getPlayerInfo/language={language}_id={id}")
def getPlayerInfo(language: str, id: int):
    """
    Cette fonction donne les informations du joueur en fonction de la langue renseignée, le nom complet, et l'identifiant TransferMarkt renseigné. La langue doit être les 2 lettres de l'extension de domaine associée, le nom doit être le même que celui fourni par searchPlayer à savoir avec un espace de séparation et l'ID doit être sous forme numérique.
    """ 
    #return {'r' : 'r'}
    language = correctDomainExtension(language)
    domain = 'https://www.transfermarkt.' + language      
    url = domain + '/spieler/profil/spieler/' + str(id)
    #Brouillage des requêtes
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    headers = {'Content-Type': 'text/html', 'user-agent': str(userAgent)}
    response = requests.get(url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        cellsListDataTable = soup.select('div[class*="info-table info-table--right-space"]')[0].findAll('span')
        citizenshipList =[]
        match language:            
                case 'fr':
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'
                case 'co.uk' | 'us' | 'co.in' | 'co.kr'|'co.za' | 'com':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'
                case 'es' | 'com.ar' | 'co' | 'mx' | 'pe':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'
                case 'de' | 'at' | 'ch':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'  
                    marketValueTitle = 'Valeur marchande'  
                case 'it':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'                    
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'ro':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'                    
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'gr':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'                    
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'com.br' | 'pt':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'                    
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'co.id':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'                    
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'com.tr':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'be' | 'nl':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'pl':                
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
                case 'jp':
                    originNameTitle = "Nom dans le pays d'origine:"
                    fullNameTitle = "Nom complet:"
                    dateOfBirthTitle = "Naissance (âge):"
                    placeOfBirthTitle = "Lieu:"
                    heightTitle = "Taille:"
                    citizenshipTitle = 'Nationalité:'
                    positionTitle = 'Position:'
                    footTitle = 'Pied:'
                    agentTitle = 'Agent du joueur:'
                    clubTitle = 'Club actuel:'
                    inTeamSinceTitle = "Dans l'équipe depuis:"
                    contractUntilTitle = 'Contrat jusqu’à:'
                    lastProlDateTitle = 'Date de la dernière prolongation:'
                    outfitterTitle = 'Équipementier:'
                    socialMediaTitle = 'Réseaux sociaux:'
                    marketValueTitle = 'Valeur marchande'  
        careerEnded = False
        agent = None
        outfitter = None
        socialMedia = []
        originName = None
        fullName = None
        for indexCell in range(len(cellsListDataTable)):
            titleOnGoing = cellsListDataTable[indexCell].text
            if titleOnGoing == originNameTitle:
                originName = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == fullNameTitle :
                fullName = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == placeOfBirthTitle :
                placeOfBirth = cellsListDataTable[indexCell+1].text.replace('\n','')
            elif titleOnGoing == dateOfBirthTitle :
                dateOfBirthList = cellsListDataTable[indexCell+1].text.replace("\n", '').split(' ')
                dateOfBirth = dateOfBirthList[0] + ' ' + dateOfBirthList[1] + ' ' + dateOfBirthList[2]
            elif titleOnGoing == heightTitle :
                height = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == citizenshipTitle :
                imgCitizenshipList = cellsListDataTable[indexCell+1].findAll('img')
                for element in imgCitizenshipList:
                    citizenshipList.append(element['title'])
            elif titleOnGoing == positionTitle :
                position = cellsListDataTable[indexCell+1].text.replace('\n                    ','').replace('                ','')
            elif titleOnGoing == footTitle :
                foot = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == agentTitle :
                rawAgent = cellsListDataTable[indexCell+1].text.replace('\n', '')
                agent = rawAgent[0 : len(rawAgent) - 1]
            elif clubTitle in titleOnGoing :
                if "https://tmssl.akamaized.net/images/wappen/small/123.png?lm=1456997286" in str(cellsListDataTable[indexCell+1].find('img')['srcset']) :
                    careerEnded = True
                    club = None
                else:
                    careerEnded = False
                    rawClub = cellsListDataTable[indexCell+1].text.replace('\n\n\n\n', '')
                    club = rawClub[0 : len(rawClub)-1]
            elif titleOnGoing == inTeamSinceTitle :
                inTeamSince = None
            elif titleOnGoing == contractUntilTitle :
                contractUntil = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == lastProlDateTitle :
                lastProlDate = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == outfitterTitle :
                outfitter = cellsListDataTable[indexCell+1].text
            elif titleOnGoing == socialMediaTitle :
                socialMediaList = cellsListDataTable[indexCell+1].findAll('a')
                for cpt in socialMediaList :
                    socialMedia.append(cpt['href'])
        shirtNumber = None
        fullNameFromBigHeader = soup.find('h1', {'class' : 'data-header__headline-wrapper'}).text
        rawNameList = fullNameFromBigHeader.split(" ")
        rawShirtNumber = rawNameList[24]
        shirtNumber = rawShirtNumber[1 : len(rawShirtNumber)]
        if rawNameList[len(rawNameList)-4] == "" : #Si le nom complet est composé de 2 mots
            name = rawNameList[len(rawNameList)-2]
            firstname = rawNameList[len(rawNameList)-3]
        else : #Si le nom complet est composé de plus de 2 mots
            name = rawNameList[len(rawNameList)-3] + ' ' + rawNameList[len(rawNameList)-2] 
            if rawNameList[len(rawNameList)-5] == "" :
                firstname = rawNameList[len(rawNameList)-4]
            else : #Si le prénom est composé de 2 mots sans tiret les séparant (cas rare)
                firstname = rawNameList[len(rawNameList)-5] + " " + rawNameList[len(rawNameList)-4]
        #Parfois récupère un prenom-nom au lieu de Prénom Nom
        if " " not in fullName :
            fullName = firstname + ' ' + name
        firstname = firstname.replace('\n', '') 
        name = name.replace('\n', '')
        #Recherche de la valeur marchande se trouvant dans une balise indétectable par FastAPI
        description = soup.find('meta', {'name' : 'description'})['content']
        descList = description.split(' ➤ ')
        marketValue = None
        for indexElement in range(len(descList)) :
            if ':' in descList[indexElement] :
                split = descList[indexElement].split(': ')
                if split[0] == marketValueTitle :
                    marketValue = split[1]
                    break
        return {
                'transferMarktId' : id,
                'url' : url,
                'name' : name,
                'description' : description,
                'fullName' : fullName,
                'imageURL' : soup.find('img', {'class' : 'data-header__profile-image'})['src'],
                'dateOfBirth' : dateOfBirth,
                'placeOfBirth' : placeOfBirth[0 : len(placeOfBirth)-3],
                'age' : dateOfBirthList[3].replace("(",'').replace(')',''),
                'height' : height,
                'citizenship' : citizenshipList,
                'isRetired' : careerEnded,
                'position' : position,
                'foot' : foot,
                'shirtNumber' : shirtNumber,
                'club' : club,
                'marketValue' : marketValue,
                'agent' : agent,
                'outfitter' : outfitter,
                'socialMedia' : socialMedia,
                'updatedAt' : None,
                'originName' : originName,
                'inTeamSince' : inTeamSince,
                }
                #'stats' : stats
                ##'contractUntil' : contractUntil,
                ##'lastProlDate' : lastProlDate   
        
