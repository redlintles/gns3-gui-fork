# Auditoria defensiva da GUI

Escopo: código local da GUI, entradas de projeto/servidor, subprocessos e arquivos.
Não foram atacados sistemas externos nem executados payloads de código. Testes em
`tests/test_security_audit.py` usam diretórios temporários e subprocessos simulados.

## SEC01 — escape do diretório na extração de atualizações

**Confirmado; impacto alto condicionado ao controle do arquivo de atualização.**
`gns3/update_manager.py`, `UpdateManager._extractTgz`: o teste anterior baseado em
prefixo textual aceitava um destino irmão cujo nome começava pelo nome do destino.
Membros de links também não eram rejeitados. Um tar com diretório `package` e
`package/../site-packages-audit/marker.txt` escreveu um marcador fora do destino
`site-packages`, sempre dentro do diretório temporário do teste.

Caminho realista: `installDownloadedUpdates`, chamado na inicialização, processa
arquivos locais previamente baixados. Exige adulteração desse arquivo ou da cadeia
de distribuição; não foi demonstrado que abrir uma topologia forneça esse arquivo.
Um update malicioso já pode substituir código dentro do pacote, portanto corrigir
traversal não autentica atualizações nem elimina risco de supply chain.

Correção: validação completa antes da primeira extração; rejeição de caminhos
absolutos, `..`, barras invertidas, drives, múltiplas raízes, symlinks, hardlinks e
arquivos especiais. Destinos resolvidos devem permanecer sob o diretório alvo.
Filtros tarfile são usados quando disponíveis, com verificações explícitas para
Python mais antigo. Arquivos regulares e diretórios de updates válidos continuam
aceitos; links em updates passam a ser recusados intencionalmente.

Regressões: traversal para irmão, symlink/hardlink e arquivo válido seguido de
membro inválido sem sobrescrever o destino durante a validação. Não cobre mudança
concorrente do filesystem por outro processo com acesso ao diretório.

## SEC02 — dados de console alteram limites de argumentos

**Confirmado; impacto médio, podendo aumentar conforme o terminal/template.**
`gns3/telnet_console.py`, `gns3/vnc_console.py`, `gns3/spice_console.py`: substituir
nome/host/porta antes de analisar a linha de comando permite que espaços e aspas
introduzam argumentos adicionais. Com template `kitty -T {name} ...`, um nome com
espaços alterou argv, confirmado interceptando Popen. Não se demonstrou execução
arbitrária universal nem comprometimento automático ao abrir projeto.

Templates vêm das preferências locais; nomes e endpoints podem vir de dados de
projeto/servidor. A abertura do console alcança o caminho vulnerável; existe também
console automático em transições de estado quando configurado. O efeito de flags
injetadas depende do programa externo.

Correção em `gns3/utils/console_command.py`: analisa primeiro o template confiável,
substitui placeholders uma vez por argumento e passa uma lista ao Popen. Windows
usa CommandLineToArgvW; Unix usa shlex. Valida host/porta e recusa caracteres de
controle e executável derivado de dados. Recusa placeholders em código de alguns
shells conhecidos. Títulos dos presets AppleScript recebem escape nas duas camadas.

Regressões: nomes com espaços, Unicode, aspas e metacaracteres continuam um argumento;
Popen é simulado. Há testes de rejeição de endpoint e código de interpretador,
estrutura AppleScript e teste nativo Windows (ignorado no Linux).

Limitação deliberada: templates que embutem placeholders diretamente em código de
shell podem agora exigir configuração com argumentos separados. Não é um sandbox
para scripts configurados pelo usuário, nem um analisador universal de shells.
Não foram validados todos os parsers internos de terminais de terceiros. Os presets
macOS foram verificados estruturalmente, sem executar AppleScript em macOS.

## Superfícies sem vulnerabilidade confirmada nesta etapa

- Importação de projetos portáteis é delegada ao servidor; a falha de tar acima é
  do updater da GUI e não deve ser atribuída ao importador de projetos.
- Não foi encontrado caminho confirmado de pickle/eval/exec controlado por projeto.
  Checksums do histórico verificam integridade, não autenticidade.
- SVG passa por QtSvg; não se demonstrou execução de JavaScript ou exploração de
  parser nativo. Atualizar dependências continua sendo responsabilidade de distribuição.
- README pode renderizar rich text e abrir links por clique. Isso merece análise de
  esquemas permitidos, mas não houve execução automática confirmada.
- Templates de captura de pacotes, remapeamento genérico de UUID durante importação,
  parsers de terminais de terceiros e autenticação de updates precisam investigação
  adicional; não são apresentados como corrigidos.
- Não se confirmou bypass automático de TLS por projeto. A opção explícita de
  ignorar certificado não equivale a uma vulnerabilidade demonstrada.

A [documentação oficial de console](https://docs.gns3.com/docs/using-gns3/beginners/the-console-terminal)
confirma o uso de templates configuráveis. A referência histórica
[CVE-2015-2667](https://nvd.nist.gov/vuln/detail/CVE-2015-2667) trata outra versão e
outro cenário; não foi atribuída ao fork atual sem reprodução.
