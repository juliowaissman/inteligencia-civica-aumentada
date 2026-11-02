# Fase 0: fuentes verificadas y propuesta de indicadores

**Fecha:** 2 de noviembre de 2026. Todas las fuentes de este documento se descargaron del origen y se leyó el valor de México o de las 32 entidades. En `pipeline/catalogo/*.yaml` está la licencia, la cita y la nota metodológica de cada una.

## Resumen de fuentes
- **28 fuentes verificadas**, con descarga automática:
  - 15 internacionales;
  - 13 nacionales o estatales, más CONAPO, que solo se usa como denominador de población.
- **4 candidatas que requieren registro o navegador:** LAPOP, Latinobarómetro, LATINNO y OGP. Quedan fuera por ahora. Si consigues los archivos, se pueden incorporar.
- **1 descartada para el nivel estatal:** ENCUCI 2020, que solo es representativa por región. Se usa como contexto nacional.

## Criterios de selección
1. Entre 2 y 3 indicadores por dimensión. Se toma el total de cada fuente o sus componentes, nunca ambos.
2. No usar indicadores construidos con los mismos datos. Por ejemplo, el «Compromiso cívico» de IDEA se calcula con datos de V-Dem, así que solo se usa V-Dem.
3. Preferir fuentes con licencia abierta (CC0, CC BY, CC BY-SA, INEGI).
4. Los conteos absolutos se convierten a tasa por 100 mil habitantes, con la población del Banco Mundial o de CONAPO.
5. Para cada indicador se toma el año más reciente que cubra al menos el 70 % de los países de comparación (en el nivel estatal, las 32 entidades).

## IICA-I (internacional): México frente a América Latina y la OCDE (55 países)

| Dim. | Indicador | Fuente | Año | Licencia | México |
|---|---|---|---|---|---|
| 1 | Personas que usan internet (%) | Banco Mundial (UIT) | 2024 | CC BY | 83,1 |
| 1 | Matrícula terciaria (% bruto) | Banco Mundial (UNESCO) | 2023 | CC BY | 47,5 |
| 1 | Componente deliberativo | V-Dem v16 | 2025 | CC BY-SA | 0,427 |
| 2 | Participación de la sociedad civil | V-Dem v16 | 2025 | CC BY-SA | 0,49 |
| 2 | Colaboración en GitHub con otras economías (por 100 mil hab.) | GitHub Innovation Graph | 2025 | CC0 | (tasa) |
| 3 | Índice Global de IA Responsable (total) | GIRAI 2026 | 2026 | CC BY | 27,95 |
| 3 | Protección legal de la privacidad | Digital Society Project v8 | 2025 | derechos reservados | 0,81 |
| 3 | Índice de servicios en línea (OSI) | ONU E-Government | 2024 | uso no comercial | 0,764 |
| 4 | Componente participativo | V-Dem v16 | 2025 | CC BY-SA | 0,651 |
| 4 | Gobierno abierto (Factor 3) | WJP Rule of Law Index | 2026 | sin licencia declarada | 0,541 |
| 4 | Índice de e-participación (EPI) | ONU E-Government | 2024 | uso no comercial | 0,740 |
| 5 | Voz y rendición de cuentas | WGI (Banco Mundial) | 2025 | CC BY | −0,28 |
| 5 | Control de la corrupción | WGI (Banco Mundial) | 2025 | CC BY | −0,94 |
| 5 | Componente igualitario | V-Dem v16 | 2025 | CC BY-SA | 0,472 |
| 6 | Índice Global de Innovación | GII 2026 (OMPI) | 2026 | CC BY | 30,57 |
| 6 | Desarrolladores en GitHub (por 100 mil hab.) | GitHub Innovation Graph | 2025 | CC0 | (tasa) |

**Contexto, fuera del índice:** uso de IA por país (Microsoft AI Diffusion, MIT; Anthropic Economic Index, CC BY), Government AI Readiness de Oxford Insights, y habilidades digitales de la UIT, con cobertura escasa.

## IICA-N (nacional): México de 2012 a 2025, por dimensión
Se usan los mismos indicadores que tienen serie histórica: V-Dem, Banco Mundial y WGI (anuales); ONU (bienal); WJP (desde 2013); y GitHub (desde 2020). Los límites de normalización se fijan con todo el panel de comparación, para que la serie sea comparable año con año. Solo se calcula el índice agregado en los años en que las 6 dimensiones tienen dato.

## IICA-E (estatal): las 32 entidades

| Dim. | Indicador | Fuente | Año | Chihuahua | Sonora |
|---|---|---|---|---|---|
| 1 | Población de 6 años y más que usa internet (%) | ENDUTIH 2025 | 2025 | 88,8 | 88,8 |
| 1 | Hogares con computadora (%) | ENDUTIH 2025 | 2025 | 48,6 | 49,6 |
| 1 | Matrícula de educación superior (por 100 mil hab.) | ANUIES 2025-26 | 2025 | (tasa) | (tasa) |
| 2 | OSC activas en el Registro Federal (por 100 mil hab.) | Registro Federal de OSC (CLUNI) | 2025 | (tasa) | (tasa) |
| 3 | Usuarios de internet que interactúan con el gobierno (%) | ENDUTIH 2025 | 2025 | 33,4 | 32,0 |
| 3 | Trámites estatales que se pueden hacer por medios electrónicos (de 24) | CNGE 2025 | 2025 | 11 | 11 |
| 3 | Trámites transaccionales en línea (de 24) | CNGE 2025 | 2025 | 1 | 6 |
| 4 | Índice de Gobierno Abierto | Métrica de Gobierno Abierto (INAI-CIDE) | 2021 | 0,524 | 0,515 |
| 4 | Espacios de participación con deliberación o cogestión (por 100 mil hab.) | CNGE 2025, sección VI | 2025 | (tasa) | (tasa) |
| 4 | Solicitudes de información recibidas (por 100 mil hab.) | CNGE 2025 | 2025 | (tasa) | (tasa) |
| 5 | Participación electoral, presidencia 2024 (%) | INE | 2024 | 53,2 | 51,1 |
| 5 | Prevalencia de corrupción en trámites (por 100 mil; menos es mejor) | ENCIG 2025 (urbana) | 2025 | 18.420 | 18.355 |
| 5 | Confianza en el gobierno estatal (%) | ENCIG 2025 (urbana) | 2025 | 41,5 | 37,8 |
| 6 | Investigadores del SNI (por 100 mil hab.) | SECIHTI | 2025 | (tasa) | (tasa) |
| 6 | Establecimientos SCIAN 5415, diseño de sistemas (por 100 mil hab.) | DENUE | 2026 | (tasa) | (tasa) |
| 6 | Solicitudes de patente (por 100 mil hab.) | IMPI | 2025 | (tasa) | (tasa) |

**Contexto, fuera del índice:** IDD-Mex 2024 (Chihuahua 3,17; Sonora 5,24), IMCO ICE 2022, confianza en autoridades (ENVIPE) y ENCUCI 2020 por región.

## Advertencias que se publicarán
- **Solo se mide capacidad instalada y algo de activación.** Los resultados emergentes no se pueden medir con datos abiertos.
- **La dimensión 2 es débil a nivel estatal:** solo tiene un indicador (OSC).
- **La MGA 2021 es la última edición,** porque el INAI se extinguió en 2024.
- **La ENCIG es urbana.**
- **El conteo de espacios de participación del CNGE varía mucho entre ediciones.**
- **Fuentes sin licencia abierta:** DSP, ONU, WJP, MGA, INE, ANUIES, IMPI y OSC. De ellas no se publican los archivos crudos, solo los valores derivados con su cita.
