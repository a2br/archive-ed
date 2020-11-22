import os
import json
import locale
from rich import print
from rich.console import Console

import ecoledirecte as ed

console = Console()
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


def calm_exit():
    console.input(password=True)
    exit()


def fs_init():
    dirs = ['data']
    for directory in dirs:
        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except OSError:
                pass


def select_account(accounts: list):
    # Filtre les comptes de type E
    choices = list(filter(lambda account: bool(
        account['typeCompte'] == "E"), accounts))
    # Choix automatique
    choice = None
    if len(choices) > 1:
        choice = next(filter(lambda choice: choice['main'], choices))
    elif len(choices) < 1:
        choice = None
    elif len(choices) == 1:
        choice = choices[0]
    if not choice:
        # Pas de compte supporté
        print("[reverse bold red]Aucun compte compatible trouvé[/]")
        print("[red]Essayez de vous connecter avec un compte Elève.[/]")
        calm_exit()

    return choice


def format_notes(notes_response, account):
    result = {
        "anneeScolaire": account['anneeScolaireCourante'],
        "periodes": []
    }
    data = notes_response['data']
    periodes = data['periodes']
    notes = data['notes']
    for periode in periodes:
        matieres = periode['ensembleMatieres']['disciplines']
        periodeObj = {
            "nom": periode['periode'],
            "code": periode['idPeriode'],
            "examBlanc": periode['examenBlanc'],
            "debut": periode['dateDebut'],
            "fin": periode['dateFin'],
            "matieres": []
        }
        for matiere in matieres:
            matiereObj = {
                "nom": matiere['discipline'],
                "code": matiere['codeMatiere'],
                "coef": matiere['coef'],
                "notes": []
            }
            notes_cible = list(filter(
                lambda note: note['codePeriode'] == periode['idPeriode'] and note['codeMatiere'] == matiere[
                    'codeMatiere'], notes))
            for cible in notes_cible:
                cibleObj = {
                    "nom": cible['devoir'],
                    "coef": locale.atof(cible['coef']),
                    "lettre": cible['enLettre'],
                    "date": cible['date']
                }
                try:
                    cibleObj['valeur'] = (locale.atof(cible['valeur']) / locale.atof(cible['noteSur']))
                    cibleObj['classe'] = (float(cible['moyenneClasse']) / locale.atof(cible['noteSur']))
                except:
                    cibleObj['valeur'] = cible['valeur']
                    cibleObj['classe'] = cible['moyenneClasse']
                matiereObj['notes'].append(cibleObj)
            periodeObj['matieres'].append(matiereObj)

        result["periodes"].append(periodeObj)
    return result


def write_data(year_object, account):
    file_path = f"data/{account['id']}.json"

    # Récupère le fichier existant, ou en crée un nouveau
    file = []
    if os.path.isfile(file_path):
        with open(file_path) as raw_file:
            opened = json.load(raw_file)
            if isinstance(opened, list):
                file = opened
    # Détermine l'emplacement de l'item à changer
    itemToChange = None
    try:
        itemToChange = next(filter(
            lambda annee: annee['anneeScolaire'] == year_object['anneeScolaire'] and annee['classe'] == year_object[
                'classe'], file), None)
    except KeyError:
        pass
    # Edite le fichier
    if itemToChange:
        indexToChange = file.index(itemToChange)
        file[indexToChange] = year_object
    else:
        file.append(year_object)

    # Ecrit le fichier
    with open(file_path, 'w') as outfile:
        json.dump(file, outfile, indent=4)
    return file_path


def main():
    username = console.input("Identifiant: ")
    password = console.input("Mot de passe: ", password=True)
    print("Connexion...")
    login_response, token = ed.login(username, password)
    if not token:
        print(login_response['message'])
        calm_exit()
    account = select_account(login_response['data']['accounts'])
    print(f"[blue]Bonjour, [bold]{account['prenom']}[/].[/]")
    fs_init()
    # Fetch and handle notes
    print("Récupération des notes...")
    notes_response, token = ed.fetch_notes(account, token)
    if not notes_response['data']:
        print(notes_response['message'])
        calm_exit()
    print("Reformatage...")
    formatted = format_notes(notes_response, account)
    print("Sauvegarde...")
    outputPath = write_data(formatted, account)
    # Conclusion
    print(f"[reverse green]Terminé[/] Les informations sur votre année scolaire {account['anneeScolaireCourante']} ont bien été mises à jour.")
    print(f"Vérifiez vos informations dans '{outputPath}'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
