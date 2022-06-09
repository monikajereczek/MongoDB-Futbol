#!/usr/bin/python
# -*- coding: cp1250 -*-
from pymongo import MongoClient
import sys
import os
import string

import pymongo

def clear():
    os.system('cls')
def polacz_z_baza():  
    try:
        uzytkownik = input("Podaj użytkownika: ")
        haslo= input("Podaj hasło: ")
        loginstring = "mongodb+srv://"+uzytkownik+":"+haslo+"@cluster0.m9rdb.mongodb.net/Futbol?retryWrites=true&w=majority"
        print("Łącznie z bazą...")
        client=MongoClient(loginstring)
        if client.server_info()['ok']==1:
            print("Połączono z bazą")
        return client, uzytkownik
    except:
        print("Błąd łączenia się z bazą")
        sys.exit()
def wyszukaj(client):
    kolekcja=int(input(f"Wybierz, czego szukasz: \n1.Zawodnik \n2.Drużyna \n3.Mecze\n"))
    if kolekcja==1:
        nr=int(input("Podaj nr zawodnika: "))
        nazwa=input("Podaj nazwę drużyny: ")
        result= client["Futbol"]["Zawodnicy"].find({"Nr Zawodnika": nr, "Drużyna" : nazwa})
    elif kolekcja==2:
        nazwa=input("Podaj nazwę drużyny: ")
        result = client["Futbol"]["Druzyny"].find({"Nazwa": nazwa})
    elif kolekcja==3:
        print("Aby wyszukać wszystie mecze, nie wpisuj daty, wciśnij enter")
        data=input("Podaj datę meczu: ")
        druzyna=input("Podaj drużynę: ")
        if data=="":
            result = client["Futbol"]["Mecze"].aggregate([{ '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ] } }])
        else:
            result = client["Futbol"]["Mecze"].aggregate([{ '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ], "Data": {"$eq": data} } }])
    else: 
        print("Wybrano złą akcję")
    for x in result:
        print(x)
def pozycja_druzyna(client):
    druzyna=input("Podaj druzynę: ")
    pozycja=input("Podaj pozycję: ")
    result = client["Futbol"]["Zawodnicy"].find({"Pozycja":pozycja , "Drużyna": druzyna})
    print("Zawodnicy z druzyny "+druzyna+ " na pozycji "+pozycja+":")
    for x in result:
        print(x["Imię"]+" "+x["Nazwisko"])
    print()
def pozycja_druzyna_zlicz(client):
    druzyna=input("Podaj druzynę: ")
    result = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Drużyna': druzyna } }, 
                                                       { '$group': { '_id': '$Pozycja', 'counter': 
                                                       { '$count': {} } } } ])
    print("Ilość zawodników z druzyny "+druzyna+ " na pozycjach:")
    for x in result:
        print(x['_id']+" - "+str(x['counter']))
    print()
def wygrane_mecze(client):
    druzyna=input("Podaj drużynę: ")
    result = client["Futbol"]["Mecze"].aggregate([ { '$match': { '$or': [ { 'D_Domowa': { '$eq': druzyna } }, { 'D_Goscie': { '$eq': druzyna } } ] } }, 
                                                      { '$project': { 'D_Domowa': 1, 'D_Goscie': 1, 'Wynik_Domowa': 1, 'Wynik_Goscie': 1, 
                                                                     'wygrana': { '$cond': { 'if': { '$or': [ { '$and': [ { '$eq': [ '$D_Domowa', druzyna ] }, 
                                                                                                                         { '$gte': [ '$Wynik_Domowa', '$Wynik_Goscie' ] } ] }, 
                                                                                                             { '$and': [ { '$eq': [ '$D_Goscie', druzyna ] }, { '$gte': [ '$Wynik_Goscie', '$Wynik_Domowa' ] } ] } ] },
                                                                                           'then': 1, 'else': 0 } } } }, 
                                                        { '$match': { 'wygrana': { '$eq': 1 } } },
                                                        { '$project': { 'wygrana': 0 } } ])
    print("Mecze, która wygrała drużyna "+druzyna+":")
    for x in result:
        print(x['D_Domowa']+" vs "+x['D_Goscie']+" wynik: " + str(x['Wynik_Domowa'])+'-'+str(x['Wynik_Goscie']))
    print()
def rozegrane_mecze_ligi(client):
    liga=input("Podaj Ligę: ")
    result = client["Futbol"]["Mecze"].aggregate([ { '$lookup': { 'from': 'Druzyny', 'localField': 'D_Domowa', 'foreignField': 'Nazwa', 'as': 'dane' } }, 
                                                  { '$unwind': { 'path': '$dane' } }, { '$set': { 'Liga': '$dane.Liga' } }, { '$project': { 'dane': 0 } }, 
                                                  { '$match': { 'Liga': liga } }, { '$sort': { 'Data': 1 } } ])
    print("Mecze rozegrane w lidze "+liga+":")
    for x in result:
        print(str(x['Data'])+"  "+x['D_Domowa']+" vs "+x['D_Goscie']+" wynik: " + str(x['Wynik_Domowa'])+'-'+str(x['Wynik_Goscie']))
    print()
def punktowi_zawodnicy(client):
    data=input("Podaj datę meczu: ")
    druzyna=input("Podaj drużynę domową: ")
    result = client["Futbol"]["Mecze"].aggregate([{ '$match': { 'Data': data , 'D_Domowa': druzyna } } ])
    print("Zawodnicy i ich punkty:")
    for x in result:
        for y in x['Punkty_Zawodnicy_Domowa']:
            zawodnik = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Nr Zawodnika': y["Zawodnik"], 'Drużyna': druzyna } }, 
                                                            { '$project': { '_id': 0, 'Liga': 0, 'Drużyna': 0 } } ])
            for z in zawodnik:
                print(y["Typ"]+" - "+z["Imię"]+" "+z["Nazwisko"]+ " - liczba punktów: "+str(y['Liczba']))
        for y in x['Punkty_Zawodnicy_Goscie']:
            zawodnik = client["Futbol"]["Zawodnicy"].aggregate([ { '$match': { 'Nr Zawodnika': y["Zawodnik"], 'Drużyna': druzyna } }, 
                                                            { '$project': { '_id': 0, 'Liga': 0, 'Drużyna': 0 } } ])
            for z in zawodnik:
                print(y["Typ"]+" - "+z["Imię"]+" "+z["Nazwisko"]+ " - liczba punktów: "+str(y['Liczba']))
def dodaj_dokument(client):
    kolekcja=int(input(f"Wybierz, do które kolekcji chcesz dodać: \n1.Zawodnik \n2.Drużyna \n3.Mecze\n"))
    if kolekcja==1:
        try:
            imie=input("Podaj imię: ")
            nazwisko=input("Podaj nazwisko: ")
            pozycja=input("Podaj pozycję: ")
            druzyna=input("Podaj druzynę: ")
            liga=input("Podaj ligę: ")
            inne = input("Jeśli chcesz dodać coś jeszcze podaj nazwe i wartosc, oddzielajac je spacją: ")
            if len(inne)>1:
                nazwa, wartosc=inne.split()
                if wartosc.isnumeric():
                    wartosc=float(wartosc)
                result=client["Futbol"]["Zawodnicy"].insert_one({"Imię":imie, "Nazwisko":nazwisko, 
                                                     "Pozycja":pozycja, "Drużyna":druzyna, "Liga":liga, 
                                                     nazwa:wartosc})
            else:
                result=client["Futbol"]["Zawodnicy"].insert_one({"Imię":imie, "Nazwisko":nazwisko, 
                                                     "Pozycja":pozycja, "Drużyna":druzyna, "Liga":liga})
            print()
            print(result)
        except:
            print("Dodawanie do kolekcji nie powiodło się")
    elif kolekcja==2:
        try:
            nazwa=input("Podaj nazwę: ")
            liga=input("Podaj ligę: ")
            miasto=input("Podaj miasto: ")
            inne = input("Jeśli chcesz dodać coś jeszcze, podaj nazwe i wartosc, oddzielajac je spacją: ")
            if len(inne)>1:
                nazwa, wartosc=inne.split()
                if wartosc.isnumeric():
                    wartosc=float(wartosc)
                result=client["Futbol"]["Druzyny"].insert_one({"Nazwa": nazwa, "Liga":liga, 
                                                     "Miasto":miasto,nazwa:wartosc})
            else:
                result=client["Futbol"]["Druzyny"].insert_one({"Nazwa": nazwa, "Liga":liga,"Miasto":miasto })
            print()                 
            print(result)
        except:
            print("Dodawanie do kolekcji nie powiodło się")
    elif kolekcja==3:
        try:
            data=input("Podaj datę: ")
            druzyna_domowa=input("Podaj drużynę domową: ")
            druzyna_goscie=input("Podaj drużynę gości: ")
            wynik_domowa=input("Podaj wynik drużyny domowej: ")
            wynik_goscie=input("Podaj wynik drużyny gości: ")
            inne = input("Jeśli chcesz dodać coś jeszcze podaj nazwe i wartosc, oddzielajac je spacją: ")
            if len(inne)>1:
                nazwa, wartosc=inne.split()
                if wartosc.isnumeric():
                    wartosc=float(wartosc)
                result=client["Futbol"]["Mecze"].insert_one({"Data":data, "D_Domowa":druzyna_domowa, 
                                                     "D_Goscie":druzyna_goscie, "Wynik_Domowa":wynik_domowa, "Wynik_Goscie":wynik_goscie, 
                                                     nazwa:wartosc})
            else:
                result=client["Futbol"]["Mecze"].insert_one({"Data":data, "D_Domowa":druzyna_domowa, 
                                                     "D_Goscie":druzyna_goscie, "Wynik_Domowa":wynik_domowa, "Wynik_Goscie":wynik_goscie})
            print()
            print(result)
        except:
            print("Dodawanie do kolekcji nie powiodło się")
        
def zmien_dokument(): 
    kolekcja=int(input(f"Wybierz kolekcję, z której dokument chcesz aktualizować: \n1.Zawodnik \n2.Drużyna \n3.Mecze\n"))
    if kolekcja==1:
        try:
            result=client["Futbol"]["Zawodnicy"]
        except:
            print("Aktualizacja dokumentu nie powiodło się")
    elif kolekcja==2:
        try:
            result=client["Futbol"]["Druzyny"]
        except:
            print("Aktualizacja dokumentu nie powiodło się")
    elif kolekcja==3:
        try:
            result=client["Futbol"]["Mecze"]
        except:
            print("Aktualizacja dokumentu nie powiodło się")



def menu_admin():
    print("1.Wyszukaj zawodnika, drużyne lub mecz")
    print("2.Wypisz wszystkich zawodników z drużyny, grających na wybranej pozycji")
    print("3.Wypisz ilu zawodników gra na pozycji w drużynie")
    print("4.Wypisz wygrane mecze drużyny")
    print("5.Wypisz rozegrane mecze danej ligi")
    print("6.Wypisz zawodników, którzy zdobyli punkty w meczu")
    print("7.Dodaj dokument do kolekcji")
    print("8.Aktualizuj istniejący dokument")
    print("10.Zakończ")
    return int(input("Wybierz akcję: "))  

def menu_zawodnik():
    print("1.Wyszukaj zawodnika, drużyne lub mecz")
    print("2.Wypisz wszystkich zawodników z drużyny, grających na wybranej pozycji")
    print("3.Wypisz ilu zawodników gra na pozycji w drużynie")
    print("4.Wypisz wygrane mecze drużyny")
    print("5.Wypisz rozegrane mecze danej ligii")
    print("6.Wypisz zawodników, którze zdobyli punkty w meczu")
    print("10.Zakończ")
    return int(input("Wybierz akcję: "))



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
        elif wybor==7:
            dodaj_dokument(client)
        elif wybor==8:
            ...
        elif wybor==10:
            break

if client.server_info()['ok']==1 and uzytkownik=="zawodnik":
    clear()
    while True:
        wybor=menu_zawodnik()
        clear()
        if wybor==1:
            wyszukaj(client)
        elif wybor==2:
            pozycja_druzyna(client)
        elif wybor==3:
            pozycja_druzyna_zlicz(client)
        elif wybor==4:
            wygrane_mecze(client)
        elif wybor==5:
            rozegrane_mecze_ligi(client)
        elif wybor==6:
            punktowi_zawodnicy(client)
        elif wybor==10:
            break

    



