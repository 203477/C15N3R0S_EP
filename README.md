# Actividad 3. Implementación de operaciones con cadenas y lenguajes

### Datos de Identificación
* **Estudiante:** Ana Nickole Cisneros Herrera
* **Matrícula:** 203477
* **Nombre de la Actividad: Implementación de operaciones con cadenas y lenguajes

---

## Configuración Base y Alfabeto

Para la ejecución de los endpoints de la API, se han establecido los siguientes parámetros iniciales:

* **Alfabeto de trabajo ($\Sigma$):** `{'a', 'b'}`
* **Conjunto $L$:** `{"", 'a', 'b'}`
* **Conjunto $M$:** `{'b', 'aa'}`

> *Nota:* Símbolo $\lambda$ = cadena vacía (`""`).

---

## Endpoints y Resultados de Ejecución

### 1. Conjuntos
Implementación de operaciones básicas sobre los lenguajes $L$ y $M$.

| Operación | Endpoint Asociado | Resultado JSON |
| :--- | :--- | :--- |
| **Unión ($L \cup M$)** | `POST /lenguajes/union` | `{"", "a", "b", "aa"}` |
| **Intersección ($L \cap M$)** | `POST /lenguajes/interseccion` | `{"b"}` |
| **Diferencia ($L - M$)** | `POST /lenguajes/diferencia` | `{"", "a"}` |
| **Diferencia ($M - L$)** | `POST /lenguajes/diferencia` | `{"aa"}` |

---

### 2. Cadenas
Cálculo de productos cartesianos (concatenaciones) y potencias de lenguajes.

* **Concatenación $L \cdot M$**
  * **Método:** `POST /lenguajes/concatenar`
  * **Desarrollo:** $\{\lambda \cdot b, \lambda \cdot aa, a \cdot b, a \cdot aa, b \cdot b, b \cdot aa\}$
  * **Salida:** `{"b", "aa", "ab", "aaa", "bb", "baa"}`

* **Concatenación $M \cdot L$**
  * **Método:** `POST /lenguajes/concatenar`
  * **Desarrollo:** $\{b \cdot \lambda, b \cdot a, b \cdot b, aa \cdot \lambda, aa \cdot a, aa \cdot b\}$
  * **Salida:** `{"b", "ba", "bb", "aa", "aaa", "aab"}`

* **Potencia $M^2$**
  * **Método:** `POST /lenguajes/potencia` *(Parámetro: `k=2`)*
  * **Desarrollo:** $\{b, aa\} \times \{b, aa\}$
  * **Salida:** `{"bb", "baa", "aab", "aaaa"}`

---

### 3. Clausura de Kleene y Combinación
Generación de secuencias infinitas limitadas a los primeros $k$ elementos y resolución de expresiones combinadas.

* **Clausura de Kleene $L^*$** ($k=8$)
  * **Endpoint:** `POST /lenguajes/clausura-kleene`
  * **Descripción:** Al contener los elementos unitarios y la cadena vacía, genera el conjunto potencia de cadenas sobre $\Sigma$.
  * **Resultado:** `["", "a", "b", "aa", "ab", "ba", "bb", "aaa"]`

* **Clausura de Kleene $M^*$** ($k=8$)
  * **Endpoint:** `POST /lenguajes/clausura-kleene`
  * **Secuencia de potencias:** 
    * $M^0 = \{\lambda\}$
    * $M^1 = \{b, aa\}$
    * $M^2 = \{bb, baa, aab, aaaa\}$
    * $M^3 = \{bbb, \dots\}$
  * **Resultado:** `["", "b", "aa", "bb", "aab", "baa", "aaaa", "bbb"]`

* **Evaluación de Expresión Compleja:** $(L \cdot M) \cup (M^* \cap L^2)$
  1. **Paso A ($L \cdot M$):** `{"b", "aa", "ab", "aaa", "bb", "baa"}`
  2. **Paso B ($L^2$):** `{"", "a", "b", "aa", "ab", "ba", "bb"}`
  3. **Paso C ($M^* \cap L^2$):** `{"", "b", "aa", "bb"}`
  4. **Paso D (Unión Final):** 
     * **Resultado:** `{"", "b", "aa", "ab", "ba", "bb", "aaa", "baa"}`
