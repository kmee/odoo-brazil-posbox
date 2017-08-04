# Instalação do Servidor Odoo Brazil Posbox com SAT

## Procedimento de instalação do Odoo Brazil Posbox em ambiente de desenvolvimento

O Posbox necessita estar rodando em ambiente separado do odoo server por utilizar uma estrutura do odoo diferente (somente o odoo core/server com alguns módulos adicionais como hw_sat, hw_proxy, escpos, etc). No caso deste manual, será utilizado 1 odoo server e 1 odoo Posbox rodando em portas diferentes - Odoo server na porta 8069 e o Odoo Posbox na porta 8089.

Para tanto, utilizaremos o ambiente a seguir:
Crie o diretório odoo-dev na home do usuário:
	*$ mkdir ~/odoo-dev*
	*$ cd ~/odoo-dev*

**Onde utilizaremos:**

/home/usuario/odoo-dev/odoo-brazil-posbox - *para instalação do Posbox*

/home/usuario/odoo-dev/odoo-server - *para instalação do odoo server com os módulos customizados (kmee, oca e terceiros)*

## Instalação
**Odoo Brazil Posbox**

Repositório:

https://github.com/kmee/odoo-brazil-posbox

  *$ git clone git@github.com:kmee/odoo-brazil-posbox.git*

Executar o buildout

  *$ cd odoo-brazil-posbox*

  *$ bash init-buildout.sh*

**Importante:**|
---------------|
Até o momento, o pessoal da base4sistemas - desenvolvedora dos módulos python para SAT, manteve 2 versões do Unidecode entre os requirements do sathub, satextrato, satcfe e satcomum, portanto, é necessário manter todos com a versão 0.4.18 para não dar problemas durante a execução do buildout. Para isso, execute o comando abaixo:
  *$ sed -i 's/unidecode==0.4.19/unidecode==0.4.18/g' src/satextrato/requirements.txt*
Ou simplesmente edite o arquivo src/satextrato/requirements.txt e altere o valor da versão do unidecode.|



Após executar o init-buildout, que instalou todas as dependências para rodar o Posbox, é necessário ajustar as configurações e executar o buildout novamente. Portanto, edite o arquivo dev.cfg e informe os valores de configuração do banco de dados como usuário, senha, nome do banco, hostname/ip e porta.

Edite o arquivo buildout.cfg e altere as opções abaixo:

  *options.xmlrpc_port = 8069*

  *options.longpolling_port = 8072*

Para:

  *options.xmlrpc_port = 8079*

  *options.longpolling_port = 8082*


Por fim, execute o buildout:

  *$ ./sandbox/bin/buildout -c dev.cfg*

Dica|
----|
Para fins de teste, há uma pasta chamada test que contem um script para testar a comunicação com o SAT e a Impressora não fiscal. Para realizar o teste, edit o arquivo test/pos.py e modifique as opções: |

	from escpos.impl.epson import TMT20

Para

	from escpos.impl.bematech import MP4200TH



Após o término da execução do buildout, inicie o odoo

  *$ bin/start_odoo --load=web,hw_proxy,hw_posbox_homepage,hw_sat*

Agora, acesse o odoo

Menu Ponto de Venda → Configurações → Ponto de Vendas
Selecione o ponto de venda que você deseja configurar.



Edite as configurações conforme a imagem abaixo:




Salve as alterações e acesso o ponto de venda.

Após carregar o Ponto de Venda, será exibido um ícone semelhante ao abaixo:


 Conexão com o SAT e a Impressora funcionando corretamente

 Conexão com o servidor Odoo estabelecida e funcionando corretamente

Odoo Server [TODO]
