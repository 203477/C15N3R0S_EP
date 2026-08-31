import itertools
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Implementación de operaciones con cadenas y lenguajes")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CadenaOperacion(BaseModel):
    x: str
    y: Optional[str] = ""
    k: Optional[int] = 1

class LenguajeOperacion(BaseModel):
    L: List[str] = []
    M: Optional[List[str]] = []
    sigma: Optional[List[str]] = []
    k: Optional[int] = 0

@app.post("/cadena/concatenar")
def concatenar_cadenas(param: CadenaOperacion):
    return {
        "Operacion": "Concatenacion de cadenas",
        "x": param.x,
        "y": param.y,
        "Resultado": param.x + (param.y or "")
    }

@app.post("/cadena/unir")
def unir_cadenas(param: CadenaOperacion):
    return {
        "Operacion": "Union de cadenas (caracteres)",
        "x": param.x,
        "y": param.y,
        "Resultado": set(param.x).union(set(param.y or ""))
    }

@app.post("/cadena/potencia")
def potencia_cadena(param: CadenaOperacion):
    if (param.k or 0) <= 0:
        res = ""
    else:
        res = param.x * (param.k or 0)
    return {
        "Operacion": "Potencia de cadena",
        "x": param.x,
        "k": param.k,
        "Resultado": res
    }

def _concatenar_conjuntos(conjunto_a: set, conjunto_b: set) -> set:
    resultado = set()
    for a in conjunto_a:
        for b in conjunto_b:
            resultado.add(a + b)
    return resultado

def _potencia_lenguaje(lenguaje: set, k: int) -> set:
    if k == 0:
        return {""}
    actual = {""}
    for _ in range(k):
        actual = _concatenar_conjuntos(actual, lenguaje)
    return actual

def generar_universo(sigma: set, k: int) -> set:
    universo = {""}
    for longitud in range(1, k + 1):
        for comb in itertools.product(sigma, repeat=longitud):
            universo.add("".join(comb))
    return universo

@app.post("/lenguajes/union")
def union_lenguajes(param: LenguajeOperacion):
    L, M = set(param.L), set(param.M or [])
    return {
        "Operacion": "Union de lenguajes",
        "L": L,
        "M": M,
        "Resultado": sorted(list(L.union(M)))
    }

@app.post("/lenguajes/interseccion")
def interseccion_lenguajes(param: LenguajeOperacion):
    L, M = set(param.L), set(param.M or [])
    return {
        "Operacion": "Interseccion de lenguajes",
        "L": L,
        "M": M,
        "Resultado": sorted(list(L.intersection(M)))
    }

@app.post("/lenguajes/diferencia")
def diferencia_lenguajes(param: LenguajeOperacion):
    L, M = set(param.L), set(param.M or [])
    return {
        "Operacion": "Diferencia de lenguajes (L - M)",
        "L": L,
        "M": M,
        "Resultado": sorted(list(L.difference(M)))
    }

@app.post("/lenguajes/concatenar")
def concatenar_lenguajes(param: LenguajeOperacion):
    L, M = set(param.L), set(param.M or [])
    return {
        "Operacion": "Concatenacion de lenguajes",
        "L": L,
        "M": M,
        "Resultado": sorted(list(_concatenar_conjuntos(L, M)))
    }

@app.post("/lenguajes/potencia")
def potencia_lenguaje_endpoint(param: LenguajeOperacion):
    L = set(param.L)
    k = param.k if param.k is not None else 0
    return {
        "Operacion": f"Potencia de lenguaje L^{k}",
        "L": L,
        "k": k,
        "Resultado": sorted(list(_potencia_lenguaje(L, k)))
    }

@app.post("/lenguajes/complemento")
def complemento_lenguaje(param: LenguajeOperacion):
    sigma = set(param.sigma or [])
    k = param.k if param.k is not None else 0
    L = set(param.L)
    universo = generar_universo(sigma, k)
    return {
        "Operacion": "Complemento de Lenguaje",
        "L": L,
        "sigma": sigma,
        "k": k,
        "Resultado": sorted(list(universo.difference(L)))
    }

@app.post("/lenguajes/clausura-kleene")
def clausura_kleene(param: LenguajeOperacion):
    """
    Genera los elementos de L* en orden de longitud hasta alcanzar param.k elementos.
    """
    L = set(param.L)
    limite = param.k if (param.k and param.k > 0) else 8
    
    elementos = {""}
    grado = 1
    
    while len(elementos) < limite and grado <= 10:
        potencia_actual = _potencia_lenguaje(L, grado)
        elementos.update(potencia_actual)
        grado += 1
        
    resultado_ordenado = sorted(list(elementos), key=lambda s: (len(s), s))[:limite]
    return {
        "Operacion": f"Clausura de Kleene (Primeros {limite} elementos)",
        "L": L,
        "Resultado": resultado_ordenado
    }