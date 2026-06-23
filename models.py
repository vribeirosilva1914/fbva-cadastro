from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False, default='operador')
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    PERFIS = {
        'admin':        'Administrador',
        'secretaria':   'Secretaria',
        'comunicacao':  'Comunicação',
        'operador':     'Operador',   # legado — mantido para compatibilidade
    }

    def nome_perfil(self):
        return self.PERFIS.get(self.perfil, self.perfil)

    def pode_editar(self):
        return self.perfil in ('admin', 'secretaria', 'comunicacao', 'operador')

    def pode_excluir(self):
        return self.perfil == 'admin'

    def pode_gerenciar_usuarios(self):
        return self.perfil == 'admin'

    def pode_ver_restrito(self):
        """Acesso a financeiro (trimestralidades) e documentação: apenas admin e secretaria."""
        return self.perfil in ('admin', 'secretaria')


class Clube(db.Model):
    __tablename__ = 'clubes'

    id = db.Column(db.Integer, primary_key=True)
    nome_clube = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    nome_presidente = db.Column(db.String(100), nullable=True)
    data_nascimento_presidente = db.Column(db.Date, nullable=True)
    data_fundacao = db.Column(db.Date, nullable=True)
    contato_preferencial = db.Column(db.String(100), nullable=True)
    fim_mandato = db.Column(db.Date, nullable=True)
    endereco = db.Column(db.String(300), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    telefone_celular = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    instagram = db.Column(db.String(150), nullable=True)
    facebook = db.Column(db.String(150), nullable=True)
    site = db.Column(db.String(150), nullable=True)
    youtube = db.Column(db.String(150), nullable=True)
    tiktok = db.Column(db.String(150), nullable=True)
    logo_filename = db.Column(db.String(300), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])
    membros_diretoria = db.relationship('MembroDiretoria', backref='clube',
                                         cascade='all, delete-orphan',
                                         order_by='MembroDiretoria.ordem')
    documentos = db.relationship('Documento', backref='clube',
                                  cascade='all, delete-orphan')
    enderecos_adicionais = db.relationship('EnderecoAdicional', backref='clube',
                                            cascade='all, delete-orphan')
    contatos = db.relationship('Contato', backref='clube',
                                cascade='all, delete-orphan')
    associados = db.relationship('Associado', backref='clube',
                                  cascade='all, delete-orphan')

    ESTADOS = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]

    def mandato_vencido(self):
        if self.fim_mandato is None:
            return False
        return self.fim_mandato < datetime.utcnow().date()

    def mandato_proximo_vencimento(self):
        if self.fim_mandato is None:
            return False
        from datetime import timedelta
        return (self.fim_mandato - datetime.utcnow().date()).days <= 60


class MembroDiretoria(db.Model):
    __tablename__ = 'membros_diretoria'

    id = db.Column(db.Integer, primary_key=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14))
    email = db.Column(db.String(150))
    whatsapp = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    ordem = db.Column(db.Integer, default=0)


class Documento(db.Model):
    __tablename__ = 'documentos'

    id = db.Column(db.Integer, primary_key=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50))
    filename = db.Column(db.String(300))
    tamanho = db.Column(db.Integer)
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    enviado_por = db.relationship('Usuario', foreign_keys=[enviado_por_id])


class EnderecoAdicional(db.Model):
    __tablename__ = 'enderecos_adicionais'

    id = db.Column(db.Integer, primary_key=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.String(100))
    logradouro = db.Column(db.String(300))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))


class Contato(db.Model):
    __tablename__ = 'contatos'

    id = db.Column(db.Integer, primary_key=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    nome = db.Column(db.String(150))
    cargo = db.Column(db.String(50))
    descricao = db.Column(db.String(100))
    telefones = db.relationship('ContatoTelefone', backref='contato',
                                 cascade='all, delete-orphan')
    emails_lista = db.relationship('ContatoEmail', backref='contato',
                                    cascade='all, delete-orphan')


class ContatoTelefone(db.Model):
    __tablename__ = 'contato_telefones'

    id = db.Column(db.Integer, primary_key=True)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id', ondelete='CASCADE'), nullable=False)
    numero = db.Column(db.String(20))
    tipo = db.Column(db.String(20), default='whatsapp')


class ContatoEmail(db.Model):
    __tablename__ = 'contato_emails'

    id = db.Column(db.Integer, primary_key=True)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(150))
    tipo = db.Column(db.String(20), default='principal')


class Associado(db.Model):
    __tablename__ = 'associados'

    id = db.Column(db.Integer, primary_key=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14))
    whatsapp = db.Column(db.String(20))
    email = db.Column(db.String(150))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class Trimestralidade(db.Model):
    __tablename__  = 'trimestralidades'
    __table_args__ = (db.UniqueConstraint('clube_id', 'ano', 'trimestre'),)

    id                = db.Column(db.Integer, primary_key=True)
    clube_id          = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'), nullable=False)
    ano               = db.Column(db.Integer, nullable=False)
    trimestre         = db.Column(db.Integer, nullable=False)   # 1-4
    status            = db.Column(db.String(20), default='pendente')  # pago | pendente | vencido
    valor             = db.Column(db.Numeric(10, 2), nullable=True)
    data_vencimento   = db.Column(db.Date, nullable=True)
    data_pagamento    = db.Column(db.Date, nullable=True)
    observacoes           = db.Column(db.Text, nullable=True)
    comprovante_filename  = db.Column(db.String(300), nullable=True)
    registrado_por_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    atualizado_em         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clube           = db.relationship('Clube', backref='trimestralidades')
    registrado_por  = db.relationship('Usuario', foreign_keys=[registrado_por_id])


class FinanceiroClube(db.Model):
    __tablename__ = 'financeiro_clubes'

    id                  = db.Column(db.Integer, primary_key=True)
    clube_id            = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='CASCADE'),
                                     nullable=False, unique=True)
    situacao            = db.Column(db.String(20), default='em_dia')   # em_dia | pendente | inadimplente
    valor_anuidade      = db.Column(db.Numeric(10, 2), nullable=True)
    vencimento_anuidade = db.Column(db.Date, nullable=True)
    observacoes         = db.Column(db.Text, nullable=True)
    atualizado_em       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    atualizado_por_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    clube           = db.relationship('Clube', backref=db.backref('financeiro', uselist=False))
    atualizado_por  = db.relationship('Usuario', foreign_keys=[atualizado_por_id])

    SITUACOES = {'em_dia': 'Em dia', 'pendente': 'Pendente', 'inadimplente': 'Inadimplente'}


class Config(db.Model):
    __tablename__ = 'config'
    chave = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Text, nullable=True)


class EmailLog(db.Model):
    __tablename__ = 'email_log'
    id             = db.Column(db.Integer, primary_key=True)
    clube_nome     = db.Column(db.String(200), nullable=False)
    destinatario   = db.Column(db.String(150))
    assunto        = db.Column(db.String(300))
    mensagem       = db.Column(db.Text)
    status         = db.Column(db.String(10), default='ok')   # ok | erro
    erro           = db.Column(db.Text)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    enviado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    enviado_por    = db.relationship('Usuario', foreign_keys=[enviado_por_id])


class WaLog(db.Model):
    __tablename__ = 'wa_log'

    id = db.Column(db.Integer, primary_key=True)
    clube_nome = db.Column(db.String(200), nullable=False)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='SET NULL'), nullable=True)
    mensagem = db.Column(db.Text, nullable=False)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)

    enviado_por = db.relationship('Usuario', foreign_keys=[enviado_por_id])


class ContatoWA(db.Model):
    """Contato externo que envia mensagens via WhatsApp."""
    __tablename__ = 'contatos_wa'

    id        = db.Column(db.Integer, primary_key=True)
    numero    = db.Column(db.String(30), unique=True, nullable=False)  # E.164 sem '+'
    nome      = db.Column(db.String(150))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    conversas = db.relationship('ConversacaoWA', backref='contato',
                                 cascade='all, delete-orphan')


class ConversacaoWA(db.Model):
    """Thread de conversa entre um contato externo e um (ou mais) agentes."""
    __tablename__ = 'conversas_wa'

    STATUS = {
        'nova':           'Nova',
        'em_atendimento': 'Em atendimento',
        'resolvida':      'Resolvida',
    }

    id            = db.Column(db.Integer, primary_key=True)
    contato_id    = db.Column(db.Integer,
                               db.ForeignKey('contatos_wa.id', ondelete='CASCADE'),
                               nullable=False)
    status        = db.Column(db.String(20), default='nova', nullable=False)
    agente_id     = db.Column(db.Integer,
                               db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                               nullable=True)
    criada_em     = db.Column(db.DateTime, default=datetime.utcnow)
    atualizada_em = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)

    agente    = db.relationship('Usuario', foreign_keys=[agente_id])
    mensagens = db.relationship('MensagemWA', backref='conversa',
                                 cascade='all, delete-orphan',
                                 order_by='MensagemWA.enviado_em')


class MensagemWA(db.Model):
    """Mensagem individual dentro de uma ConversacaoWA."""
    __tablename__ = 'mensagens_wa'

    id             = db.Column(db.Integer, primary_key=True)
    conversa_id    = db.Column(db.Integer,
                                db.ForeignKey('conversas_wa.id', ondelete='CASCADE'),
                                nullable=False)
    direcao        = db.Column(db.String(10), nullable=False)   # entrada | saida
    corpo          = db.Column(db.Text, nullable=False)
    wa_message_id  = db.Column(db.String(100), nullable=True, unique=True)
    enviado_por_id = db.Column(db.Integer,
                                db.ForeignKey('usuarios.id', ondelete='SET NULL'),
                                nullable=True)
    enviado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    lida           = db.Column(db.Boolean, default=False)

    enviado_por = db.relationship('Usuario', foreign_keys=[enviado_por_id])


class ClippingNoticia(db.Model):
    __tablename__ = 'clipping_noticias'

    id            = db.Column(db.Integer, primary_key=True)
    titulo        = db.Column(db.String(500), nullable=False)
    url           = db.Column(db.String(1000), nullable=False, unique=True)
    fonte         = db.Column(db.String(200))
    resumo        = db.Column(db.Text)
    publicado_em  = db.Column(db.DateTime)
    coletado_em   = db.Column(db.DateTime, default=datetime.utcnow)
    palavra_chave = db.Column(db.String(100))
    bloco         = db.Column(db.String(30), default='radar')   # radar|mercado|eventos|restauracao|gente|juridico
    nivel         = db.Column(db.Integer, default=1)            # 1=especializada 2=geral 3=tecnica
    lida          = db.Column(db.Boolean, default=False)


class Evento(db.Model):
    __tablename__ = 'eventos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=True)
    imagem_filename = db.Column(db.String(300), nullable=True)
    local = db.Column(db.String(200), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    clube_id = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='SET NULL'), nullable=True)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    diretor_representante = db.Column(db.String(150), nullable=True)
    trofeu_status         = db.Column(db.String(20),  nullable=True, default='nao_enviado')
    trofeu_enviado_em     = db.Column(db.Date,        nullable=True)
    trofeu_observacoes    = db.Column(db.Text,        nullable=True)

    clube = db.relationship('Clube', backref=db.backref('eventos', lazy='dynamic'))
    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])


class RecorrenciaConteudo(db.Model):
    __tablename__ = 'recorrencias_conteudo'

    DIAS = [
        (0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),  (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    id            = db.Column(db.Integer, primary_key=True)
    titulo        = db.Column(db.String(200), nullable=False)
    dia_semana    = db.Column(db.Integer,     nullable=False)   # 0=seg … 6=dom
    plataforma    = db.Column(db.String(30),  nullable=False)
    tipo_conteudo = db.Column(db.String(30),  nullable=True)
    descricao     = db.Column(db.Text,        nullable=True)
    status_padrao = db.Column(db.String(20),  nullable=False, default='agendado')
    ativa         = db.Column(db.Boolean,     nullable=False, default=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)


class AgendaConteudo(db.Model):
    __tablename__ = 'agenda_conteudo'

    PLATAFORMAS = [
        ('instagram', 'Instagram'),
        ('facebook',  'Facebook'),
        ('whatsapp',  'WhatsApp'),
        ('youtube',   'YouTube'),
        ('email',     'E-mail'),
        ('site',      'Site'),
        ('outro',     'Outro'),
    ]
    TIPOS = [
        ('post',              'Post'),
        ('story',             'Story'),
        ('reels',             'Reels'),
        ('carrossel',         'Carrossel'),
        ('video',             'Vídeo'),
        ('email_newsletter',  'E-mail / Newsletter'),
        ('mensagem',          'Mensagem'),
        ('artigo',            'Artigo / Notícia'),
        ('outro',             'Outro'),
    ]
    STATUS = [
        ('rascunho',  'Rascunho'),
        ('agendado',  'Agendado'),
        ('publicado', 'Publicado'),
        ('cancelado', 'Cancelado'),
    ]

    id              = db.Column(db.Integer, primary_key=True)
    titulo          = db.Column(db.String(200), nullable=False)
    plataforma      = db.Column(db.String(30),  nullable=False)
    tipo_conteudo   = db.Column(db.String(30),  nullable=True)
    data_publicacao = db.Column(db.Date,        nullable=False)
    hora_publicacao = db.Column(db.String(5),   nullable=True)   # HH:MM
    status          = db.Column(db.String(20),  nullable=False, default='rascunho')
    descricao       = db.Column(db.Text,        nullable=True)
    responsavel_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    evento_id       = db.Column(db.Integer, db.ForeignKey('eventos.id',  ondelete='SET NULL'), nullable=True)
    clube_id        = db.Column(db.Integer, db.ForeignKey('clubes.id',   ondelete='SET NULL'), nullable=True)
    criado_por_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id])
    evento      = db.relationship('Evento',  foreign_keys=[evento_id])
    clube       = db.relationship('Clube',   foreign_keys=[clube_id])
    criado_por  = db.relationship('Usuario', foreign_keys=[criado_por_id])


class DiretorFBVA(db.Model):
    __tablename__ = 'diretores_fbva'

    GRUPOS = [
        ('diretoria_executiva',   'Diretoria Executiva'),
        ('conselho_consultivo',   'Conselho Consultivo'),
        ('conselho_fiscal',       'Conselho Fiscal'),
        ('diretorias_regionais',  'Diretorias Regionais'),
        ('diretoria_tecnica',     'Diretoria Técnica'),
        ('diretorias_auxiliares', 'Diretorias Auxiliares'),
        ('fundo_solidariedade',   'Fundo de Solidariedade'),
    ]

    CARGOS = {
        'diretoria_executiva':   ['Presidente', 'Vice-Presidente Administrativo',
                                  'Vice-Presidente Jurídico', 'Vice-Presidente Financeiro',
                                  'Vice-Presidente Técnico'],
        'conselho_consultivo':   ['Presidente do Conselho Consultivo', 'Conselheiro Consultivo'],
        'conselho_fiscal':       ['Conselheiro Fiscal'],
        'diretorias_regionais':  ['Diretor Regional'],
        'diretoria_tecnica':     ['Diretor Técnico'],
        'diretorias_auxiliares': ['Diretor Esportivo', 'Diretor de Assuntos Internacionais',
                                  'Diretor de Cultura e Juventude', 'Diretor de Assuntos Institucionais'],
        'fundo_solidariedade':   ['Presidente'],
    }

    id              = db.Column(db.Integer, primary_key=True)
    nome            = db.Column(db.String(150), nullable=False)
    grupo           = db.Column(db.String(50),  nullable=False)
    cargo           = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(150), nullable=True)
    telefone        = db.Column(db.String(20),  nullable=True)
    cpf             = db.Column(db.String(14),  nullable=True)
    data_nascimento = db.Column(db.Date,        nullable=True)
    cidade          = db.Column(db.String(100), nullable=True)
    estado          = db.Column(db.String(2),   nullable=True)
    ativo           = db.Column(db.Boolean, default=True, nullable=False)
    ordem           = db.Column(db.Integer, default=0)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])

    def grupo_label(self):
        return dict(self.GRUPOS).get(self.grupo, self.grupo)


class TicketOuvidoria(db.Model):
    __tablename__ = 'tickets_ouvidoria'

    TIPOS = [
        ('sugestao',   'Sugestão'),
        ('reclamacao', 'Reclamação'),
        ('elogio',     'Elogio'),
        ('informacao', 'Informação'),
        ('denuncia',   'Denúncia'),
    ]
    STATUS = [
        ('aberto',       'Aberto'),
        ('em_andamento', 'Em andamento'),
        ('aguardando',   'Aguardando retorno'),
        ('resolvido',    'Resolvido'),
        ('fechado',      'Fechado'),
    ]
    PRIORIDADES = [
        ('baixa',   'Baixa'),
        ('media',   'Média'),
        ('alta',    'Alta'),
        ('urgente', 'Urgente'),
    ]

    id                   = db.Column(db.Integer, primary_key=True)
    protocolo            = db.Column(db.String(20), unique=True, nullable=False)
    tipo                 = db.Column(db.String(20), nullable=False)
    assunto              = db.Column(db.String(200), nullable=False)
    descricao            = db.Column(db.Text, nullable=False)
    nome_solicitante     = db.Column(db.String(150), nullable=True)
    email_solicitante    = db.Column(db.String(150), nullable=True)
    telefone_solicitante = db.Column(db.String(20),  nullable=True)
    clube_id             = db.Column(db.Integer, db.ForeignKey('clubes.id', ondelete='SET NULL'), nullable=True)
    status               = db.Column(db.String(20), default='aberto', nullable=False)
    prioridade           = db.Column(db.String(10), default='media',  nullable=False)
    responsavel_id       = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    resolucao            = db.Column(db.Text,     nullable=True)
    resolucao_em         = db.Column(db.DateTime, nullable=True)
    criado_em            = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clube       = db.relationship('Clube',   foreign_keys=[clube_id])
    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id])
    respostas   = db.relationship('TicketResposta', backref='ticket',
                                   cascade='all, delete-orphan',
                                   order_by='TicketResposta.criado_em')


class TicketResposta(db.Model):
    __tablename__ = 'ticket_respostas'

    id        = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets_ouvidoria.id', ondelete='CASCADE'), nullable=False)
    autor_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    texto     = db.Column(db.Text, nullable=False)
    interno   = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    autor = db.relationship('Usuario', foreign_keys=[autor_id])


class DocumentoFBVA(db.Model):
    __tablename__ = 'documentos_fbva'

    TIPOS = [
        ('estatuto',    'Estatuto'),
        ('ata',         'Ata'),
        ('regimento',   'Carta de São Paulo'),
        ('resolucao',   'Documentos Legislativos'),
        ('portaria',    'Manual do Vistoriador'),
        ('convenio',    'Contratos'),
        ('manual_proc', 'Manual de Procedimento Administrativo'),
        ('outro',       'Outro'),
    ]

    id             = db.Column(db.Integer, primary_key=True)
    nome           = db.Column(db.String(200), nullable=False)
    tipo           = db.Column(db.String(20),  nullable=False)
    descricao      = db.Column(db.Text,        nullable=True)
    ano            = db.Column(db.Integer,     nullable=True)
    vigente        = db.Column(db.Boolean,     default=False)
    filename       = db.Column(db.String(300), nullable=True)
    tamanho        = db.Column(db.Integer,     nullable=True)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    enviado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enviado_por = db.relationship('Usuario', foreign_keys=[enviado_por_id])


class RelatorioFinanceiro(db.Model):
    __tablename__ = 'relatorios_financeiros'

    STATUS = [
        ('rascunho',  'Rascunho'),
        ('aprovado',  'Aprovado'),
        ('publicado', 'Publicado'),
    ]

    id            = db.Column(db.Integer, primary_key=True)
    ano           = db.Column(db.Integer, nullable=False)
    trimestre     = db.Column(db.Integer, nullable=False)
    titulo        = db.Column(db.String(200), nullable=False)
    descricao     = db.Column(db.Text,        nullable=True)
    status        = db.Column(db.String(20),  default='rascunho', nullable=False)
    filename      = db.Column(db.String(300), nullable=True)
    tamanho       = db.Column(db.Integer,     nullable=True)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))
