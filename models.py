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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))
