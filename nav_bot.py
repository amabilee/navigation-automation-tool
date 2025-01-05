import sys
import time
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from functools import partial
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QMessageBox, QScrollArea, QHBoxLayout

class Worker(QThread):
    update_status = pyqtSignal(str)
    finished = pyqtSignal()
    paused = pyqtSignal()
    automacao_concluida = pyqtSignal()

    def __init__(self, intervalo, links, id_automacao):
        super().__init__()
        self.intervalo = intervalo
        self.links = links
        self.running = True
        self.driver = None
        self.current_index = 0
        self.id_automacao = id_automacao

    def start_driver(self):
        self.update_status.emit("Iniciando navegador...")
        options = uc.ChromeOptions()
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        self.driver = uc.Chrome(options=options)
    
    def run(self):
        print(self)
        try:
            self.start_driver()  # Inicializa o navegador
            print("Navegador iniciado.")

            while self.running and self.current_index < len(self.links):
                link = self.links[self.current_index]
                print(f"Iniciando navegação para o link {self.current_index + 1}/{len(self.links)}: {link}")

                try:
                    # Verifica se o navegador ainda está aberto
                    if not self.driver:
                        self.update_status.emit("Navegador não detectado. Reiniciando...")
                        print("Navegador não encontrado. Reiniciando...")
                        self.start_driver()

                    self.update_status.emit(f"Abrindo: {link}")
                    print(f"Acessando o link: {link}")
                    self.driver.get(link)  # Acessa o link diretamente

                    # Aguarda a página carregar completamente
                    try:
                        WebDriverWait(self.driver, self.intervalo).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        self.update_status.emit(f"Página carregada: {link}")
                        print(f"Página carregada: {link}")
                    except Exception as e:
                        self.update_status.emit(f"Erro ao carregar página: {link} - {str(e)}")
                        print(f"Erro ao carregar página: {link} - {str(e)}")
                     
                    for j in range(self.intervalo, 0, -1):
                        if not self.running:
                            self.update_status.emit("Automação parada.")
                            print("Automação parada.")
                            if self.driver:
                                self.driver.quit()
                            return

                        self.update_status.emit(f"Tempo restante: {j} segundos")
                        print(f"Tempo restante: {j} segundos")
                        time.sleep(1)

                    # Incrementa o índice do link processado
                    self.current_index += 1
                    print(f"Indo para o próximo link. Índice atual: {self.current_index}")

                except WebDriverException as e:
                    self.update_status.emit(f"Erro ao acessar o link: {link}. Reiniciando navegador...")
                    print(f"Erro ao acessar o link: {link}. Reiniciando navegador...")
                    self.start_driver()  # Reinicia o navegador em caso de erro crítico

            # Finaliza a automação ao terminar os links
            self.update_status.emit("Automação concluída!")
            print("Automação concluída!")
            if self.driver:
                self.driver.quit()

            # Emite o sinal de conclusão
            self.automacao_concluida.emit()  # Emite o sinal

        except Exception as e:
            self.update_status.emit(f"Erro durante a execução: {str(e)}")
            print(f"Erro durante a execução: {str(e)}")
        finally:
            self.finished.emit()
            print("Execução finalizada.")
    
    def stop(self):
        self.running = False
        if self.driver:
            self.driver.quit()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.automacoes = []  # Lista para armazenar as automações cadastradas
        self.id_automacao = 1  # Identificador único para cada automação
        self.cadastro_ativo = False  # Flag para verificar se o cadastro está ativo
        self.edicao_ativo = False  # Flag para verificar se a edicao está ativo

    def init_ui(self):
        self.setWindowTitle("Automação de Navegação")
        self.setGeometry(300, 100, 500, 500)

        # Layout principal
        layout = QVBoxLayout()

        # Botão para adicionar automação
        self.botao_adicionar = QPushButton("Adicionar Automação", self)
        self.botao_adicionar.clicked.connect(self.adicionar_automacao)
        layout.addWidget(self.botao_adicionar)

        # Área para exibir as automações cadastradas
        self.area_automacoes = QScrollArea(self)
        self.layout_automacoes = QVBoxLayout()
        self.area_automacoes.setLayout(self.layout_automacoes)
        layout.addWidget(self.area_automacoes)

        # Definir o layout
        self.setLayout(layout)

    def adicionar_automacao(self):
        if self.cadastro_ativo:
            return  # Se já há um cadastro em andamento, não permite adicionar mais um

        self.cadastro_ativo = True  # Marca que o cadastro está ativo

        # Criação de um novo popup (QDialog)
        popup_automacao = QDialog(self)
        popup_automacao.setWindowTitle("Adicionar Automação")

        nova_automacao_layout = QVBoxLayout()

        # Campo para inserir os links
        texto_links = QTextEdit(popup_automacao)
        texto_links.setPlaceholderText("Insira os links separados por vírgula")
        nova_automacao_layout.addWidget(texto_links)

        # Campo para inserir o intervalo
        entry_intervalo = QLineEdit(popup_automacao)
        entry_intervalo.setPlaceholderText("Intervalo entre os links (em segundos)")
        nova_automacao_layout.addWidget(entry_intervalo)

        # Botão para salvar a automação
        botao_salvar = QPushButton("Salvar Automação", popup_automacao)
        botao_salvar.clicked.connect(lambda: self.salvar_automacao(texto_links, entry_intervalo, popup_automacao))
        nova_automacao_layout.addWidget(botao_salvar)

        # Botão para cancelar o cadastro
        botao_cancelar = QPushButton("Cancelar", popup_automacao)
        botao_cancelar.clicked.connect(lambda: self.cancelar_automacao(popup_automacao))
        nova_automacao_layout.addWidget(botao_cancelar)

        # Configurar o layout no QDialog
        popup_automacao.setLayout(nova_automacao_layout)

        # Exibir o popup
        popup_automacao.exec_()
    
    def cancelar_automacao(self, nova_automacao):
        self.cadastro_ativo = False  # Permite adicionar novas automações
        self.layout_automacoes.removeWidget(nova_automacao)
        nova_automacao.deleteLater()

    def salvar_automacao(self, texto_links, entry_intervalo, nova_automacao):
        links = texto_links.toPlainText().strip()
        intervalo = entry_intervalo.text().strip()

        if not links or not intervalo:
            QMessageBox.critical(self, "Erro", "Por favor, insira os links e o intervalo.")
            return

        try:
            intervalo = int(intervalo)
        except ValueError:
            QMessageBox.critical(self, "Erro", "O intervalo deve ser um número inteiro.")
            return

        # Preparar lista de links
        lista_links = [link.strip() for link in links.split(',')]

        # Criar a nova automação
        automacao = {
            "id": self.id_automacao,
            "links": lista_links,
            "intervalo": intervalo,
            "status": "Pendente",
            "worker": None  # Inicialmente sem worker
        }
        self.automacoes.append(automacao)

        # Atualizar a tela para exibir as automações cadastradas
        self.atualizar_lista_automacoes()

        # Limpar os campos
        texto_links.clear()
        entry_intervalo.clear()

        # Aumenta o ID para a próxima automação
        self.id_automacao += 1

        # Fechar o campo de cadastro de automação
        self.layout_automacoes.removeWidget(nova_automacao)
        nova_automacao.deleteLater()
        self.cadastro_ativo = False  # Permite que o usuário inicie um novo cadastro

    def atualizar_lista_automacoes(self):
        # Limpar a lista de automações exibida
        for i in reversed(range(self.layout_automacoes.count())):
            widget = self.layout_automacoes.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Adicionar cada automação à lista
        for automacao in self.automacoes:
            automacao_widget = QWidget()
            automacao_layout = QHBoxLayout()

            automacao_layout.addWidget(QLabel(f"Automação {automacao['id']}"))
            automacao_layout.addWidget(QLabel(automacao["status"]))

            # Botão para iniciar
            if automacao["status"] == "Pendente" or automacao["status"] == "Finalizada":
                botao_iniciar = QPushButton("Iniciar", self)
                botao_iniciar.clicked.connect(partial(self.iniciar_automacao, automacao["id"]))
                automacao_layout.addWidget(botao_iniciar)

            # Botão para finalizar
            if automacao["status"] == "Em Execução":
                botao_finalizar = QPushButton("Finalizar", self)
                botao_finalizar.clicked.connect(partial(self.finalizar_automacao, automacao["id"]))
                automacao_layout.addWidget(botao_finalizar)

            # Botão para editar
            if automacao["status"] == "Pendente" or automacao["status"] == "Finalizada":
                botao_editar = QPushButton("Editar", self)
                botao_editar.clicked.connect(lambda: self.editar_automacao(automacao["id"]))
                automacao_layout.addWidget(botao_editar)

            # Adiciona a automação à lista
            automacao_widget.setLayout(automacao_layout)
            self.layout_automacoes.addWidget(automacao_widget)

    def iniciar_automacao(self, id_automacao):
        # Encontra a automação com o id especificado
        automacao = next((a for a in self.automacoes if a["id"] == id_automacao), None)
        
        if not automacao:
            QMessageBox.critical(self, "Erro", "Automação não encontrada!")
            return

        # Verifica se já existe um worker em execução para esta automação
        if "worker" in automacao and automacao["worker"] is not None:
            if automacao["worker"].isRunning():
                QMessageBox.warning(self, "Aviso", "Esta automação já está em execução!")
                return

        # Cria e inicia o worker para a automação
        worker = Worker(automacao["intervalo"], automacao["links"], automacao["id"])
        worker.finished.connect(lambda: self.automacao_finalizada(automacao["id"]))
        worker.automacao_concluida.connect(lambda: self.automacao_finalizada(automacao["id"]))
        automacao["worker"] = worker  # Salva o worker associado à automação
        automacao["status"] = "Em Execução"  # Atualiza o status da automação
        worker.start()  # Inicia o worker
        
        self.atualizar_lista_automacoes()  # Atualiza a lista de automações na interface

    def finalizar_automacao(self, id_automacao):
        automacao = next((a for a in self.automacoes if a["id"] == id_automacao), None)
        if automacao and automacao["worker"]:
            automacao["worker"].stop()
            automacao["status"] = "Finalizada"
            self.atualizar_lista_automacoes()

    def editar_automacao(self, id_automacao):
        if self.edicao_ativo:
            return  # Se já há uma edição em andamento, não permite abrir um novo pop-up

        self.edicao_ativo = True  # Marca que a edição está ativa

        # Encontra a automação com o id especificado
        automacao = next((a for a in self.automacoes if a["id"] == id_automacao), None)
        
        if not automacao or automacao["status"] == "Em Execução":
            QMessageBox.warning(self, "Aviso", "Esta automação não pode ser editada no momento!")
            self.edicao_ativo = False  # Permite abrir a edição novamente
            return
        
        # Criação de um novo popup (QDialog) para edição
        popup_automacao = QDialog(self)
        popup_automacao.setWindowTitle(f"Editar Automação - {id_automacao}")

        editar_automacao_layout = QVBoxLayout()

        # Campo para inserir os links (pré-preenchido com os links da automação)
        texto_links = QTextEdit(popup_automacao)
        texto_links.setPlainText(", ".join(automacao["links"]))  # Preenche com os links atuais
        editar_automacao_layout.addWidget(texto_links)

        # Campo para editar o intervalo (pré-preenchido com o valor atual)
        entry_intervalo = QLineEdit(popup_automacao)
        entry_intervalo.setText(str(automacao["intervalo"]))  # Preenche com o intervalo atual
        editar_automacao_layout.addWidget(entry_intervalo)

        # Botão para salvar as alterações
        botao_salvar = QPushButton("Salvar Alterações", popup_automacao)
        botao_salvar.clicked.connect(lambda: self.salvar_edicao(automacao, texto_links, entry_intervalo, popup_automacao))
        editar_automacao_layout.addWidget(botao_salvar)

        # Botão para cancelar a edição
        botao_cancelar = QPushButton("Cancelar", popup_automacao)
        botao_cancelar.clicked.connect(lambda: self.cancelar_edicao(popup_automacao))
        editar_automacao_layout.addWidget(botao_cancelar)

        # Configurar o layout no QDialog
        popup_automacao.setLayout(editar_automacao_layout)

        # Exibir o pop-up
        popup_automacao.exec_()

    def cancelar_edicao(self, popup_automacao):
        self.edicao_ativo = False  # Permite adicionar ou editar novas automações
        popup_automacao.close()

    def salvar_edicao(self, automacao, texto_links, entry_intervalo, popup_automacao):
        links = texto_links.toPlainText().strip()
        intervalo = entry_intervalo.text().strip()

        if not links or not intervalo:
            QMessageBox.critical(self, "Erro", "Por favor, insira os links e o intervalo.")
            return

        try:
            intervalo = int(intervalo)
        except ValueError:
            QMessageBox.critical(self, "Erro", "O intervalo deve ser um número inteiro.")
            return

        # Preparar lista de links
        lista_links = [link.strip() for link in links.split(',')]

        # Atualizar os dados da automação
        automacao["links"] = lista_links
        automacao["intervalo"] = intervalo

        # Atualizar a interface para refletir as mudanças
        self.atualizar_lista_automacoes()

        # Fechar o pop-up de edição
        popup_automacao.close()
        self.edicao_ativo = False  # Permite novas edições


    def automacao_finalizada(self, id_automacao):
        # Encontra a automação com o id especificado
        automacao = next((a for a in self.automacoes if a["id"] == id_automacao), None)
        if automacao:
            automacao["status"] = "Finalizada"  # Atualiza o status da automação
        
        self.atualizar_lista_automacoes()

app = QApplication(sys.argv)
ex = App()
ex.show()
sys.exit(app.exec_())
