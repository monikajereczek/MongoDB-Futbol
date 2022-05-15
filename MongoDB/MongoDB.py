#!/usr/bin/python
# -*- coding: cp1250 -*-
from pymongo import MongoClient
import sys
import os

def clear():
    os.system('cls')
def polacz_z_baza():  
    try:
        uzytkownik = input("Podaj u�ytkownika: ")
        haslo= input("Podaj has�o: ")
        loginstring = "mongodb+srv://"+uzytkownik+":"+haslo+"@cluster0.m9rdb.mongodb.net/Futbol?retryWrites=true&w=majority"
        print("��cznie z baz�...")
        client=MongoClient(loginstring)
        if client.server_info()['ok']==1:
            print("Po��czono z baz�")
        return client, uzytkownik
    except:
        print("B��d ��czenia si� z baz�")
        sys.exit()

def wyszukaj(client):
    kolekcja=int(input(f"Wybierz czego szukasz: \n1.Zawodnik \n2.Dru�yna \n3.Mecze\n"))
    if kolekcja==1:
        nr=int(input("Podaj nr zawodnika: "))
        nazwa=input("Podaj nazw� dru�yny: ")
        result= client["Futbol"]["Zawodnicy"].find({"Nr Zawodnika": nr, "Dru�yna" : nazwa})
    elif kolekcja==2:
        nazwa=input("Podaj nazw� dru�yny: ")
        result = client["Futbol"]["Druzyny"].find({"Nazwa": nazwa})
    elif kolekcja==3:
        print("Aby wyszuka� wszystie mecze, nie wpisuj daty, wci�nij enter")
        data=input("Podaj dat� meczu: ")
        druzyna=input("Podaj dru�yn�: ")
        if data=="":
            result = client["Futbol"]["Mecze"].aggregate([{ '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ] } }])
        else:
            result = client["Futbol"]["Mecze"].aggregate([{ '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ], "Data": {"$eq": data} } }])
    else: 
        print("Wybrano z�� akcj�")
    for x in result:
        print(x)

           

        
   
def pozycja_druzyna(client):
    druzyna=input("Podaj druzyn�: ")
    pozycja=input("Podaj pozycj�: ")
    result = client["Futbol"]["Zawodnicy"].find({"Pozycja":pozycja , "Dru�yna": druzyna})
    print("Zawodnicy z druzyny "+druzyna+ " na pozycji "+pozycja+":")
    for x in result:
        print(x["Imi�"]+" "+x["Nazwisko"])
    print()
def pozycja_druzyna_zlicz(client):
    druzyna=input("Podaj druzyn�: ")
    result = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Dru�yna': druzyna } }, 
                                                       { '$group': { '_id': '$Pozycja', 'counter': 
                                                       { '$count': {} } } } ])
    print("Ilo�� zawodnik�w z druzyny "+druzyna+ " na pozycjach:")
    for x in result:
        print(x['_id']+" - "+str(x['counter']))
    print()
def wygrane_mecze(client):
    druzyna=input("Podaj dru�yn�: ")
    result = client["Futbol"]["Mecze"].aggregate([ { '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ] } }, 
                                                      { '$project': { 'D_Domowa': 1, 'D_Goscie': 1, 'Wynik_Domowa': 1, 'Wynik_Goscie': 1, 
                                                                     'wygrana': { '$cond': { 'if': { '$or': [ { '$and': [ { '$eq': [ '$D_Domowa', druzyna ] }, 
                                                                                                                         { '$gte': [ '$Wynik_Domowa', '$Wynik_Goscie' ] } ] }, 
                                                                                                             { '$and': [ { '$eq': [ '$D_Goscie', druzyna ] }, { '$gte': [ '$Wynik_Goscie', '$Wynik_Domowa' ] } ] } ] },
                                                                                           'then': 1, 'else': 0 } } } }, 
                                                        { '$match': { 'wygrana': { '$eq': 1 } } },
                                                        { '$project': { 'wygrana': 0 } } ])
    print("Mecze, kt�ra wygra�a dru�yna "+druzyna+":")
    for x in result:
        print(x['D_Domowa']+" vs "+x['D_Goscie']+" wynik: " + str(x['Wynik_Domowa'])+'-'+str(x['Wynik_Goscie']))
    print()
def rozegrane_mecze_ligi(client):
    liga=input("Podaj Lig�: ")
    result = client["Futbol"]["Mecze"].aggregate([ { '$lookup': { 'from': 'Druzyny', 'localField': 'D_Domowa', 'foreignField': 'Nazwa', 'as': 'dane' } }, 
                                                  { '$unwind': { 'path': '$dane' } }, { '$set': { 'Liga': '$dane.Liga' } }, { '$project': { 'dane': 0 } }, 
                                                  { '$addFields': { 'Data': { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$Data' } } } }, 
                                                  { '$match': { 'Liga': liga } }, { '$sort': { 'Data': 1 } } ])
    print("Mecze, rezegrane w lidze "+liga+":")
    for x in result:
        print(str(x['Data'])+"  "+x['D_Domowa']+" vs "+x['D_Goscie']+" wynik: " + str(x['Wynik_Domowa'])+'-'+str(x['Wynik_Goscie']))
    print()
def punktowi_zawodnicy(client):
    data=input("Podaj dat� meczu: ")
    druzyna=input("Podaj dru�yn� domow�: ")
    result = client["Futbol"]["Mecze"].aggregate([{ '$match': { 'Data': data , 'D_Domowa': druzyna } } ])
    print("Zawodnicy i ich punkty:")
    for x in result:
        for y in x['Punkty_Zawodnicy_Domowa']:
            zawodnik = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Nr Zawodnika': y["Zawodnik"], 'Dru�yna': druzyna } }, 
                                                            { '$project': { '_id': 0, 'Liga': 0, 'Dru�yna': 0 } } ])
            for z in zawodnik:
                print(y["Typ"]+" - "+z["Imi�"]+" "+z["Nazwisko"]+ " - liczba punkt�w: "+str(y['Liczba']))
        for y in x['Punkty_Zawodnicy_Goscie']:
            zawodnik = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Nr Zawodnika': y["Zawodnik"], 'Dru�yna': druzyna } }, 
                                                            { '$project': { '_id': 0, 'Liga': 0, 'Dru�yna': 0 } } ])
            for z in zawodnik:
                print(y["Typ"]+" - "+z["Imi�"]+" "+z["Nazwisko"]+ " - liczba punkt�w: "+str(y['Liczba']))
    
def menu_admin():
    
    print("1.Wyszukaj zawodnika, dru�yne lub mecz")
    print("2.Wypisz wszystkich zawodnik�w z dru�yny, graj�cych na wybranej pozycji")
    print("3.Wypisz ilu zawodnik�w gra na pozycji w dru�ynie")
    print("4.Wypisz wygrane mecze dru�yny")
    print("5.Wypisz rozegrane mecze danej ligii")
    print("6.Zawodnicy, kt�rze zdobyli punkty w meczu")
    print("7.Dodaj dokument do dowolnej kolekcji")
    print("8.Edutuj istniej�cy dokument")
    print("10.Zako�cz")
    return int(input("Wybierz akcj�: "))        
def menu_zawodnik():
    print("1.Wypisz wszystkich zawodnik�w z dru�yny, graj�cych na wybranej pozycji")
    print("2.Wypisz ilu zawodnik�w gra na pozycji w dru�ynie")
    print("3.Wypisz wygrane mecze dru�yny")
    print("4.Wypisz rozegrane mecze danej ligii")
    print("5.Zawodnicy, kt�rze zdobyli punkty w meczu")
    print("10.Zako�cz")
    return int(input("Wybierz akcj�: "))
client, uzytkownik=polacz_z_baza()

if client.server_info()['ok']==1 and uzytkownik=="python":
    clear()
    while True:
        wybor=menu_admin()
        clear()
        if wybor==1:
            wyszukaj(client)
        elif wybor==2:
            pozycja_druzyna(client)
        elif wybor ==3:
            pozycja_druzyna_zlicz(client)
        elif wybor==4:
            wygrane_mecze(client)
        elif wybor==5:
            rozegrane_mecze_ligi(client)
        elif wybor==6:
            punktowi_zawodnicy(client)
        elif wybor==10:
            break

if client.server_info()['ok']==1 and uzytkownik=="zawodnik":
    clear()
    while True:
        wybor=menu_zawodnik()
        clear()
        if wybor==1:
            wyszukaj(client)
        elif wybor ==2:
            pozycja_druzyna_zlicz(client)
        elif wybor==3:
            wygrane_mecze(client)
        elif wybor==4:
            rozegrane_mecze_ligi(client)
        elif wybor==5:
            punktowi_zawodnicy(client)
        elif wybor==10:
            break

    



