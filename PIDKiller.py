# Modulos
import PySimpleGUI as Sg
import wmi
from smb.SMBConnection import SMBConnection
from configparser import ConfigParser
from time import sleep
import sys
from multiprocessing import Process, freeze_support

# Variavel de controle do While (sair = 1 finaliza o programa)
sair = 0

# Carrega o arquivo de configuração
cfg = ConfigParser()
cfg.read('config.ini')
comp = cfg.get('Server', 'IP')
user = cfg.get('Server', 'user')
passwd = cfg.get('Server', 'passwd')

# Layout de tela
Sg.theme('Reddit')
layout = [[Sg.Text('PID Killer'), Sg.Text('Servidor:'), Sg.Text(comp)],
          [Sg.Output(size=(90, 30), key='-OUTPUT-')],
          [Sg.Button('Carregar Pool'), Sg.Button('Carregar Task'), Sg.Button('Sair')],
          [Sg.Text('Qual PID deseja finalizar?'), Sg.Input(key='input'), Sg.Button('Finalizar Processo')]]

window = Sg.Window('PIDKiller', layout, icon='icon.ico')


# Function de Loading
def _splash():
    for i in range(500000):
        Sg.PopupAnimated('load.gif', background_color='white', time_between_frames=60)
    # noinspection PyTypeChecker
    Sg.PopupAnimated(None)


# Function Principal
def _program():
    # Cria a conexão WMI usando os dados informados, para executar comandos remotos
    try:
        remoto = wmi.WMI(comp, user=user, password=passwd)
        local = wmi.WMI()
    except wmi.x_wmi:
        sleep(3)
        Sg.popup("Atenção, não foi possível conectar ao servidor! Verifique as configurações!", title="Atenção!")
        sys.exit(1)

    # Executa o comando definido, gerando um arquivo TXT na raiz disco
    remoto.Win32_Process.Create(CommandLine='cmd.exe /c C:/Windows/System32/inetsrv/appcmd.exe list wp >> '
                                            '"C:/InfoPool.txt"')
    remoto.Win32_Process.Create(CommandLine='cmd.exe /c tasklist >> "C:/InfoList.txt"')

    # Realiza a conexão SMB com a maquina remota para copia dos arquivos para a maquina local
    conn = SMBConnection(user, passwd, 'client', comp)
    conn.connect(comp, 139, timeout=10000)

    global sair
    while sair := 0:

        with open('C:/InfoOutPool.txt', 'wb') as fp1:
            sleep(1)
            conn.retrieveFile('C$', '/InfoPool.txt', fp1)

        arquivo1 = open('C:/InfoOutPool.txt', 'r')
        listapool = arquivo1.read()
        arquivo1.close()

        with open('C:/InfoOutList.txt', 'wb') as fp2:
            sleep(1)
            conn.retrieveFile('C$', '/InfoList.txt', fp2)

        arquivo2 = open('C:/InfoOutList.txt', 'r')
        listatask = arquivo2.read()
        arquivo2.close()

        sleep(1)

        # Eventos da Interface Gráfica
        while True:

            (event, values) = window.read(timeout=100)

            if event == 'Carregar Task':
                window['-OUTPUT-'].update(listatask)

            if event == 'Carregar Pool':
                window['-OUTPUT-'].update(listapool)

            if event == Sg.WIN_CLOSED or event == 'Sair':
                remoto.Win32_Process.Create(CommandLine='cmd.exe /c DEL "C:/Info*.txt"')
                local.Win32_Process.Create(CommandLine='cmd.exe /c DEL "C:/Info*.txt"')
                Sg.popup_auto_close('Saindo...', auto_close_duration=2, button_type=5, no_titlebar=True)
                sair = 1
                break

            if event == 'Finalizar Processo':
                processo = values['input']
                killer = str(processo)
                remoto.Win32_Process.Create(CommandLine="cmd.exe /b /c taskkill -pid " + killer + " /f")
                Sg.popup_ok('Processo Finalizado com Sucesso!')

        break

    conn.close()
    window.close()


if __name__ == '__main__':
    freeze_support()
    load = Process(target=_splash)
    exe = Process(target=_program)
    jobs = [load, exe]
    for job in jobs:
        job.start()
