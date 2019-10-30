from oda.evaluate import evaluate
import click
from click_alias import ClickAliasedGroup


@click.group(cls=ClickAliasedGroup)
def oda():
    pass

@oda.command(aliases=["i","in","info"])
def info():
    click.echo("oda evaluate")

@oda.command(aliases=["ev","eva","eval", "evaluate"])
@click.argument('target', nargs=1)
@click.argument('graphs', nargs=-1)
def evaluate_cli(target, graphs):
    return evaluate(target, *graphs)
        

@oda.command()
def oda_list(aliases=["l","li","list"]):
    click.echo("oda list")


def rdf():
    pass

def apidocs():
    if router == "odahub":
        return requests.get("https://oda-workflows-fermilat.odahub.io/apispec_1.json").json()


def module():
    pass

def module():
    #symmetric interoperability with astroquery
    pass

if __name__ == "__main__":
    oda()
