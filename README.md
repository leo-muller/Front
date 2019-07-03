# Split de Ordens

- [Base de Dados](#id-SQL)
    - [Ativos](#id-SQL-Ativos)
    - [Grupos](#id-SQL-Grupos)
    - [Ordens](#id-SQL-Ordens)
- [Arquivos Python](#id-pythonFile)

# Base de dados <a name="id-SQL"></a>

Informações sobre a base de dados

## Ativos <a name='id-SQL-Ativos'></a>
Tabelas referentes a quebra de ordem por grupos / familias

#### Trade_Asset_Info

Tabela com as informações basicas dos ativos

Nome | Tipo | Info
-----|------|------
TickerID  | int | id IDENTITY(1,1) (PK)
TickerMitra | varchar(100) | Ticker Mitra
TickerBlg | varchar(100) | Ticker Bloomberg
TickerBroker | varchar(100) | Ticker Itau ou Bradesco
TickerType | varchar(20) | Forma de tratar o ativo

TickerType pode ser:
* **FX_B3**: Moedas na B3
* **FX_M_B3**: Mini contrato de moedas na B3
* **FX_CME**: Moedas na CME
* **OPT_DOL_B3**: Opção de dolar B3

#### Trade_Asset_Info_Aux

Informacoes adicionais sobre ativos

Nome | Tipo | Info
-----|------|------
TickerAuxID  | int | id IDENTITY(1,1) (PK)
TickerID | int | Ticker do ativo
TickerInfo | varchar(100) | Campo Informacao
TickerInfoVal | varchar(100) | Valor da informacao

TickerInfo pode ser entre outros:
* **Vencimento**: Vencimento do ativo (em geral ultimo dia de PnL)
* **FX_Pair**: Par relativo do ativo
* **Size**: Tamanho do contrato (notional no caso de moedas)
* **Factor**: Fator Multiplicativo para quote blg
* **Factor_RJO**: Fator multiplicativo de pricing da RJO
* **OptType**: Call ou Put
* **OptStrike**: Strike (K)
* **OptCode**: Codigo B3

#### Trade_Asset_Ts_Id

Para o mesmo ativo podemos ter varias series

Nome | Tipo | Info
-----|------|------
TickerTsID  | int | id IDENTITY(1,1) (PK)
TickerID | int | Ativo (FK)
**TsField** | varchar(50) | Tipo de serie

**TsField** pode ser por exemplo:
* **quote**: Preco oficial blg
* **quoteEst**: Preco com feed de planilha

#### Trade_Asset_Ts

Series de tempo para os ativos

Nome | Tipo | Info
-----|------|------
TsID  | int | id IDENTITY(1,1) (PK)
TickerTsID  | int | id IDENTITY(1,1) (PK)
Date0 | date | data
Value | float | Valor 

#### Trade_Asset_Template_Excel
Tabela para gerar tickers usando nomeclatura template, deletada diariamente

Nome | Tipo | Info
-----|------|------
TickerTemplateId  | int | id IDENTITY(1,1) (PK)
TickerTemplate | varchar(100) | Nome da classe de template do arquivo
TickerMitraCore | varchar(100) | Ticker Mitra
TickerBrokerCore | varchar(100) | Ticker Itau ou Bradesco
TickerBlgCore | varchar(100) | Inicio do ticker blg
TickerBlgSufix | varchar(100) | Sulfixo do ticker blg
TickerType | varchar(100) | Forma de tratar o ativo
TickerTypeGen | varchar(100) | Forma de gerar o ticker / split

#### Trade_Asset_Template_RJO

Tabela auxiliar para importar futuros direto do arquivo da RJO

Nome | Tipo | Info
-----|------|------
RjoId  | int | id IDENTITY(1,1) (PK)
MitraPrefix | varchar(10) | Prefixo ticker Mitra
MitraSufix | varchar(10) | Sulfixo ticker Mitra
Blg | varchar(10) | Prefixo Ticker Blg
RJO | varchar(50) | Nome no site RJO
FactRJO | int | Fator entre preço RJO e Blg

#### Trade_Corretora
Tabela com as corretoras

Nome | Tipo | Info
-----|------|------
CorretoraID  | int | Numero Itau (PK)
CorretoraExcel | varchar(100) | Nome da corretora no Excel
CorretoraMitra | varchar(100) | Nome da corretora no Mitra

# Grupos <a name='id-SQL-Grupos'></a>
Tabelas referentes a quebra de ordem por grupos / familias

#### Trade_Grupos_Info

Tabela com as informações basicas dos grupos criados pela mesa

Nome | Tipo | Info
-----|------|------
GroupId | int | id DENTITY(1,1) (PK)
GroupName | varchar(100) | Nome no grupo
GroupInfo | varchar(200) | Motivo de criação do grupo
GroupDate | date | Data de criação DEFAULT CONVERT(char(10),GETDATE(),126)
Owner0 | varchar(100) | Maquina que criou o grupo


#### Trade_Grupos_Detail

Tabela com detalhes do grupo

Nome | Tipo | Info
-----|------|------
GroupSplitId | int | id IDENTITY(1,1) (PK)
GroupId | int | Id do grupo (FK)
FundoId | int | Codigo do Fundo (FK)
Quant | float | Se quebramos a quantidade exata do fundo
Ratio | float | Se quebramos por multiplicador

#### Trade_Grupos_Raw

Tabela salva pelos traders que vai gerar Front_Grupos_Info e Front_Grupos_Detail

Nome | Tipo | Info
-----|------|------
GroupRawId | int | id DENTITY(1,1) (PK)
GroupName | varchar(100) | Nome no grupo
FundoNome | varchar(200) | Nome do fundo (FK) mmFundo Pre_Grupos
Quant | float | Se quebramos a quantidade exata do fundo
Ratio | float | Se quebramos por multiplicador
GroupInfo | varchar(200) | Motivo de criação do grupo
Date0 | date | Data de criação DEFAULT CONVERT(char(10),GETDATE(),126)
Owner0 | varchar(100) | Maquina que criou o grupo

#### Pre_Grupos
Tabela na base bd_risco com as informações dos fundos e grupo padrão os campos que usamos são

Nome | Info
-----|------
GrupoId | Id do grupo
Grupo | Nome do Grupo
FundoID | Id do fundo
mmFundo | Nome do Fundo (FundoNome)
vlPatrimonio | AUM
Participacao | % da ordem target para o fundo
CD_Carteira | Codigo MITRA
CD_CCI | CCI do fundo


## Ordens <a name='id-SQL-Ordens'></a>
Tabela com as ordens

#### Trade_Orders_Raw

Tabela com as informações basicas dos grupos criados pela mesa

Nome | Tipo | Info
-----|------|------
OrderRawId | int | id DENTITY(1,1) (PK)
C_V | varchar(1) | Compra ou venda
TickerRaw | varchar(100) | Pode ser o ticker Mitra ou um template
Vencimento | date | Vencimento
Quantidade | int | Quantidade
Preco | float | Preco do ativo
CorretoraExcel | varchar(100) | Nome da corretora
Est1 | varchar(50) | Estrategia 1
Est2 | varchar(50) | Estrategia 2
Est3 | varchar(50) | Estrategia 3
GrupoRaw | varchar(50) | Grupo padrao ou novo
PrecoAux | float | Preco auxiliar (como base de rolagem)
**FillType** | varchar(50) | Como vamos distribuir a ordem
FillAsset | varchar(50) | Ativo usado como referenica para o split
FillEst | varchar(50) | Estrategia 3 usada como referencia
TradeRational | varchar(255) | Informações sobre o trade
Owner0 | varchar(100) | Quem criou o trade
Date0 | date | DEFAULT CONVERT(char(10),GETDATE(),126)

**FillType** pode ser:
* **new**: distribui usando somente o trade
* **position**: considera o estoque total, não so o trade
* **relative**: usa algum ativo de referencia, como por exemplo para delta, ou tornar B em BE.

#### Trade_Orders

Tabela com as informações trabalhadas de trade

Nome | Tipo | Info
-----|------|------
OrderId | int | id IDENTITY(1,1) (PK)
TickerId | int | Ativo (FK)
Quantidade | int | Quantidade (positiva ou negativa)
Preco | float | Preco do ativo
CorretoraId | int | Corretora
Est1 | varchar(50) | Estrategia 1
Est2 | varchar(50) | Estrategia 2
Est3 | varchar(50) | Estrategia 3
GrupoType | varchar(50) | Grupo padrao ou novo
GrupoId | int | Id do grupo (FK)
**SaveType** | varchar | Tipo de registro de ordem
FillType | varchar(50) | Como vamos distribuir a ordem
FillAsset | varchar(50) | Ativo usado como referenica para o split
FillEst | varchar(50) | Estrategia 3 usada como referencia
TradeRational | varchar(255) | Informações sobre o trade
Owner0 | varchar(100) | Quem criou o trade
Date0 | date | DEFAULT CONVERT(char(10),GETDATE(),126)

**SaveType** trades como rolagem precisamos salvar a rolagem (para o Itau) e o trade aberto (para o Mitra) 
então temos:
* **Itau**: Salvo apenas no Itau (DR1 por exemplo)
* **MitraFut**: Salvo apenas no Mitra (C/V de Dol de DR1, futuro offshore)
* **MitraOpc**: Salvo apenas no Mitra na aba opc (Opcao de Bolsa)
* **ItauMitraFut**: Salvo no itau e aba futuro Mitra (DI, UCA, IND..)
* **ItauMitraOpt**: Salvo no itau e aba Opc Mitra (Opc FX, DDI...)




#### Trade_Orders_Split

Tabela com as informações trabalhadas de trade

Nome | Tipo | Info
-----|------|------
OrderSplitId | int | id IDENTITY(1,1) (PK)
OrderId | int | Ordem original (FK)
FundoID | int | Fundo (FK)
Quant | int | Quantidade

## Arquivos <a name="id-pythonFile"></a>
Teste
