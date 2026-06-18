import os
import uuid
import requests as http
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import (Usuario, Clube, WaLog, EmailLog, Config, FinanceiroClube,
                    Trimestralidade, MembroDiretoria, Documento,
                    EnderecoAdicional, Contato, ContatoTelefone, ContatoEmail,
                    Associado, ClippingNoticia)

api_bp = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'}
WA_SERVICE = os.environ.get('WA_SERVICE_URL', 'http://localhost:3001')


# ── helpers ─────────────────────────────────────────────────────────────────
def ok(data=None, code=200, **kw):
    return jsonify({'ok': True, 'data': data, **kw}), code

def err(msg, code=400):
    return jsonify({'ok': False, 'error': msg}), code

def parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None

def fmt_size(n):
    if not n:
        return '—'
    if n < 1024:
        return f'{n} B'
    if n < 1024 * 1024:
        return f'{n/1024:.1f} KB'
    return f'{n/1024/1024:.1f} MB'


def clube_dict(c):
    criador = c.criado_por
    return {
        'id':                  c.id,
        'nomeClube':           c.nome_clube,
        'cnpj':                c.cnpj,
        'nomePresidente':      c.nome_presidente,
        'dataNascimentoPresidente': c.data_nascimento_presidente.isoformat() if c.data_nascimento_presidente else None,
        'dataFundacao':        c.data_fundacao.isoformat() if c.data_fundacao else None,
        'contatoPreferencial': c.contato_preferencial,
        'fimMandato':          c.fim_mandato.isoformat() if c.fim_mandato else None,
        'endereco':            c.endereco,
        'cidade':              c.cidade,
        'estado':              c.estado,
        'telefoneCelular':     c.telefone_celular,
        'email':               c.email,
        'instagram':           c.instagram,
        'facebook':            c.facebook,
        'site':                c.site,
        'youtube':             c.youtube,
        'tiktok':              c.tiktok,
        'observacoes':         c.observacoes,
        'ativo':               c.ativo,
        'criadoEm':            c.criado_em.isoformat()     if c.criado_em     else None,
        'atualizadoEm':        c.atualizado_em.isoformat() if c.atualizado_em else None,
        'criadoPorId':         c.criado_por_id,
        'criadoPorNome':       criador.nome if criador else None,
        'numMembros':          len(c.membros_diretoria),
        'numDocs':             len(c.documentos),
        'numAssociados':       len(c.associados),
    }


def membro_dict(m):
    return {
        'id':             m.id,
        'cargo':          m.cargo,
        'nome':           m.nome,
        'cpf':            m.cpf,
        'email':          m.email,
        'whatsapp':       m.whatsapp,
        'dataNascimento': m.data_nascimento.isoformat() if m.data_nascimento else None,
        'ordem':          m.ordem,
    }

def documento_dict(d):
    return {
        'id':            d.id,
        'nome':          d.nome,
        'tipo':          d.tipo,
        'filename':      d.filename,
        'tamanho':       d.tamanho,
        'tamanhoFmt':    fmt_size(d.tamanho),
        'enviadoEm':     d.enviado_em.isoformat() if d.enviado_em else None,
        'enviadoPorNome': d.enviado_por.nome if d.enviado_por else None,
    }

def endereco_dict(e):
    return {
        'id':         e.id,
        'tipo':       e.tipo,
        'descricao':  e.descricao,
        'logradouro': e.logradouro,
        'cidade':     e.cidade,
        'estado':     e.estado,
    }

def contato_dict(c):
    return {
        'id':        c.id,
        'nome':      c.nome,
        'cargo':     c.cargo,
        'descricao': c.descricao,
        'telefones': [{'id': t.id, 'numero': t.numero, 'tipo': t.tipo} for t in c.telefones],
        'emails':    [{'id': e.id, 'email': e.email, 'tipo': e.tipo} for e in c.emails_lista],
    }

def associado_dict(a):
    return {
        'id':        a.id,
        'nome':      a.nome,
        'cpf':       a.cpf,
        'whatsapp':  a.whatsapp,
        'email':     a.email,
        'ativo':     a.ativo,
        'criadoEm':  a.criado_em.isoformat() if a.criado_em else None,
    }

def clube_full_dict(c):
    d = clube_dict(c)
    d['membros']             = [membro_dict(m)     for m   in c.membros_diretoria]
    d['documentos']          = [documento_dict(doc) for doc in c.documentos]
    d['enderecosAdicionais'] = [endereco_dict(e)   for e   in c.enderecos_adicionais]
    d['contatos']            = [contato_dict(ct)   for ct  in c.contatos]
    d['associados']          = [associado_dict(a)  for a   in c.associados]
    return d

def usuario_dict(u):
    return {
        'id':       u.id,
        'nome':     u.nome,
        'email':    u.email,
        'perfil':   u.perfil,
        'ativo':    u.ativo,
        'criadoEm': u.criado_em.isoformat() if u.criado_em else None,
    }

def _clube_from_json(data, clube=None):
    if clube is None:
        clube = Clube()
    clube.nome_clube                  = (data.get('nomeClube') or '').strip()
    clube.cnpj                        = data.get('cnpj') or None
    clube.nome_presidente             = data.get('nomePresidente') or None
    clube.data_nascimento_presidente  = parse_date(data.get('dataNascimentoPresidente'))
    clube.data_fundacao               = parse_date(data.get('dataFundacao'))
    clube.contato_preferencial        = data.get('contatoPreferencial') or None
    clube.fim_mandato                 = parse_date(data.get('fimMandato'))
    clube.endereco                    = data.get('endereco') or None
    clube.cidade                      = data.get('cidade') or None
    clube.estado                      = data.get('estado') or None
    clube.telefone_celular            = data.get('telefoneCelular') or None
    clube.email                       = data.get('email') or None
    clube.instagram                   = data.get('instagram') or None
    clube.facebook                    = data.get('facebook') or None
    clube.site                        = data.get('site') or None
    clube.youtube                     = data.get('youtube') or None
    clube.tiktok                      = data.get('tiktok') or None
    clube.observacoes                 = data.get('observacoes') or None
    clube.ativo                       = bool(data.get('ativo', True))
    return clube


# ── AUTH ────────────────────────────────────────────────────────────────────
@api_bp.route('/me')
@login_required
def me():
    return ok(usuario_dict(current_user))


@api_bp.route('/login', methods=['POST'])
def login():
    d = request.get_json(silent=True) or {}
    email = (d.get('email') or '').strip().lower()
    senha = d.get('senha') or ''
    u = Usuario.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.senha_hash, senha):
        return err('E-mail ou senha incorretos.', 401)
    if not u.ativo:
        return err('Conta desativada. Contate o administrador.', 403)
    login_user(u, remember=bool(d.get('lembrar', False)))
    return ok(usuario_dict(u))


@api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return ok()


@api_bp.route('/senha', methods=['POST'])
@login_required
def change_password():
    d = request.get_json(silent=True) or {}
    if not check_password_hash(current_user.senha_hash, d.get('atual', '')):
        return err('Senha atual incorreta.')
    nova = d.get('nova', '')
    if len(nova) < 6:
        return err('A nova senha deve ter no mínimo 6 caracteres.')
    current_user.senha_hash = generate_password_hash(nova)
    db.session.commit()
    return ok()


# ── CLUBES ──────────────────────────────────────────────────────────────────
@api_bp.route('/clubes')
@login_required
def list_clubes():
    q      = request.args.get('q', '').strip()
    estado = request.args.get('estado', '').strip()
    status = request.args.get('status', 'ativos')

    query = Clube.query
    if status == 'ativos':
        query = query.filter_by(ativo=True)
    elif status == 'inativos':
        query = query.filter_by(ativo=False)

    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Clube.nome_clube.ilike(like),
            Clube.nome_presidente.ilike(like),
            Clube.cidade.ilike(like),
            Clube.cnpj.ilike(like),
        ))
    if estado:
        query = query.filter_by(estado=estado)

    clubes = query.order_by(Clube.nome_clube).all()
    return ok([clube_dict(c) for c in clubes])


@api_bp.route('/clubes', methods=['POST'])
@login_required
def create_clube():
    if not current_user.pode_editar():
        return err('Sem permissão para criar clubes.', 403)
    d = request.get_json(silent=True) or {}
    if not (d.get('nomeClube') or '').strip():
        return err('O nome do clube é obrigatório.')
    cnpj = d.get('cnpj') or None
    if cnpj and Clube.query.filter_by(cnpj=cnpj).first():
        return err('Já existe um clube cadastrado com este CNPJ.')
    c = _clube_from_json(d)
    c.criado_por_id = current_user.id
    db.session.add(c)
    db.session.commit()
    return ok(clube_full_dict(c), code=201)


@api_bp.route('/clubes/importar', methods=['POST'])
@login_required
def import_clubes():
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    registros = request.get_json(silent=True) or []
    importados, ignorados = 0, 0
    for d in registros:
        nome = (d.get('nomeClube') or '').strip()
        if not nome:
            ignorados += 1
            continue
        cnpj = d.get('cnpj') or None
        if cnpj and Clube.query.filter_by(cnpj=cnpj).first():
            ignorados += 1
            continue
        c = _clube_from_json(d)
        c.criado_por_id = current_user.id
        db.session.add(c)
        importados += 1
    db.session.commit()
    return ok({'importados': importados, 'ignorados': ignorados})


@api_bp.route('/clubes/<int:id>', methods=['GET'])
@login_required
def get_clube(id):
    c = db.session.get(Clube, id)
    if not c:
        return err('Clube não encontrado.', 404)
    return ok(clube_full_dict(c))


@api_bp.route('/clubes/<int:id>', methods=['PUT'])
@login_required
def update_clube(id):
    if not current_user.pode_editar():
        return err('Sem permissão para editar clubes.', 403)
    c = db.session.get(Clube, id)
    if not c:
        return err('Clube não encontrado.', 404)
    d = request.get_json(silent=True) or {}
    if not (d.get('nomeClube') or '').strip():
        return err('O nome do clube é obrigatório.')
    cnpj = d.get('cnpj') or None
    conflito = Clube.query.filter(Clube.cnpj == cnpj, Clube.id != id).first()
    if cnpj and conflito:
        return err('Já existe outro clube com este CNPJ.')
    _clube_from_json(d, c)
    db.session.commit()
    return ok(clube_full_dict(c))


@api_bp.route('/clubes/<int:id>', methods=['DELETE'])
@login_required
def delete_clube(id):
    if not current_user.pode_excluir():
        return err('Sem permissão para excluir clubes.', 403)
    c = db.session.get(Clube, id)
    if not c:
        return err('Clube não encontrado.', 404)
    # Remove uploaded files for this club's documents
    upload_dir = current_app.config['UPLOAD_FOLDER']
    for doc in c.documentos:
        try:
            os.remove(os.path.join(upload_dir, doc.filename))
        except OSError:
            pass
    db.session.delete(c)
    db.session.commit()
    return ok()


# ── MEMBROS DA DIRETORIA ─────────────────────────────────────────────────────
@api_bp.route('/clubes/<int:cid>/membros', methods=['GET'])
@login_required
def get_membros(cid):
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    return ok([membro_dict(m) for m in c.membros_diretoria])


@api_bp.route('/clubes/<int:cid>/membros', methods=['PUT'])
@login_required
def replace_membros(cid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    data = request.get_json(silent=True) or []
    MembroDiretoria.query.filter_by(clube_id=cid).delete()
    for i, m in enumerate(data):
        nome = (m.get('nome') or '').strip()
        if not nome:
            continue
        db.session.add(MembroDiretoria(
            clube_id=cid,
            cargo=m.get('cargo') or 'outro',
            nome=nome,
            cpf=m.get('cpf') or None,
            email=m.get('email') or None,
            whatsapp=m.get('whatsapp') or None,
            data_nascimento=parse_date(m.get('dataNascimento')),
            ordem=i,
        ))
    db.session.commit()
    return ok([membro_dict(m) for m in c.membros_diretoria])


# ── DOCUMENTOS ───────────────────────────────────────────────────────────────
@api_bp.route('/clubes/<int:cid>/documentos', methods=['GET'])
@login_required
def get_documentos(cid):
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    return ok([documento_dict(d) for d in c.documentos])


@api_bp.route('/clubes/<int:cid>/documentos', methods=['POST'])
@login_required
def upload_documento(cid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    if 'file' not in request.files:
        return err('Nenhum arquivo enviado.')
    f = request.files['file']
    if not f.filename:
        return err('Arquivo inválido.')
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return err('Tipo não permitido. Use PDF, DOC, DOCX ou imagens.')
    safe = secure_filename(f.filename)
    unique = f'{uuid.uuid4().hex}_{safe}'
    upload_dir = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_dir, unique)
    f.save(filepath)
    size = os.path.getsize(filepath)
    doc = Documento(
        clube_id=cid,
        nome=request.form.get('nome') or f.filename,
        tipo=request.form.get('tipo') or 'outro',
        filename=unique,
        tamanho=size,
        enviado_por_id=current_user.id,
    )
    db.session.add(doc)
    db.session.commit()
    return ok(documento_dict(doc), code=201)


@api_bp.route('/documentos/<int:did>', methods=['GET'])
@login_required
def download_documento(did):
    d = db.session.get(Documento, did)
    if not d:
        return err('Documento não encontrado.', 404)
    upload_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir, d.filename,
                               as_attachment=True, download_name=d.nome)


@api_bp.route('/documentos/<int:did>', methods=['DELETE'])
@login_required
def delete_documento(did):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    d = db.session.get(Documento, did)
    if not d:
        return err('Documento não encontrado.', 404)
    upload_dir = current_app.config['UPLOAD_FOLDER']
    try:
        os.remove(os.path.join(upload_dir, d.filename))
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    return ok()


# ── ENDEREÇOS ADICIONAIS ──────────────────────────────────────────────────────
@api_bp.route('/clubes/<int:cid>/enderecos-adicionais', methods=['PUT'])
@login_required
def replace_enderecos(cid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    data = request.get_json(silent=True) or []
    EnderecoAdicional.query.filter_by(clube_id=cid).delete()
    for e in data:
        if not (e.get('logradouro') or e.get('cidade') or e.get('descricao')):
            continue
        db.session.add(EnderecoAdicional(
            clube_id=cid,
            tipo=e.get('tipo') or 'outro',
            descricao=e.get('descricao') or None,
            logradouro=e.get('logradouro') or None,
            cidade=e.get('cidade') or None,
            estado=e.get('estado') or None,
        ))
    db.session.commit()
    return ok([endereco_dict(e) for e in c.enderecos_adicionais])


# ── CONTATOS ──────────────────────────────────────────────────────────────────
@api_bp.route('/clubes/<int:cid>/contatos', methods=['PUT'])
@login_required
def replace_contatos(cid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    data = request.get_json(silent=True) or []
    Contato.query.filter_by(clube_id=cid).delete()
    for ct_data in data:
        nome = (ct_data.get('nome') or '').strip()
        if not nome:
            continue
        ct = Contato(
            clube_id=cid,
            nome=nome,
            cargo=ct_data.get('cargo') or None,
            descricao=ct_data.get('descricao') or None,
        )
        db.session.add(ct)
        db.session.flush()
        for t in (ct_data.get('telefones') or []):
            num = (t.get('numero') or '').strip()
            if num:
                db.session.add(ContatoTelefone(
                    contato_id=ct.id,
                    numero=num,
                    tipo=t.get('tipo') or 'whatsapp',
                ))
        for em in (ct_data.get('emails') or []):
            email = (em.get('email') or '').strip()
            if email:
                db.session.add(ContatoEmail(
                    contato_id=ct.id,
                    email=email,
                    tipo=em.get('tipo') or 'principal',
                ))
    db.session.commit()
    return ok([contato_dict(ct) for ct in c.contatos])


# ── ASSOCIADOS ────────────────────────────────────────────────────────────────
@api_bp.route('/clubes/<int:cid>/associados', methods=['GET'])
@login_required
def get_associados(cid):
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    q = request.args.get('q', '').strip()
    query = Associado.query.filter_by(clube_id=cid)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Associado.nome.ilike(like),
            Associado.cpf.ilike(like),
            Associado.email.ilike(like),
        ))
    return ok([associado_dict(a) for a in query.order_by(Associado.nome).all()])


@api_bp.route('/clubes/<int:cid>/associados', methods=['POST'])
@login_required
def create_associado(cid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    c = db.session.get(Clube, cid)
    if not c:
        return err('Clube não encontrado.', 404)
    d = request.get_json(silent=True) or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return err('O nome é obrigatório.')
    a = Associado(
        clube_id=cid,
        nome=nome,
        cpf=d.get('cpf') or None,
        whatsapp=d.get('whatsapp') or None,
        email=d.get('email') or None,
        ativo=bool(d.get('ativo', True)),
    )
    db.session.add(a)
    db.session.commit()
    return ok(associado_dict(a), code=201)


@api_bp.route('/clubes/<int:cid>/associados/<int:aid>', methods=['PUT'])
@login_required
def update_associado(cid, aid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    a = Associado.query.filter_by(id=aid, clube_id=cid).first()
    if not a:
        return err('Associado não encontrado.', 404)
    d = request.get_json(silent=True) or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return err('O nome é obrigatório.')
    a.nome     = nome
    a.cpf      = d.get('cpf') or None
    a.whatsapp = d.get('whatsapp') or None
    a.email    = d.get('email') or None
    a.ativo    = bool(d.get('ativo', True))
    db.session.commit()
    return ok(associado_dict(a))


@api_bp.route('/clubes/<int:cid>/associados/<int:aid>', methods=['DELETE'])
@login_required
def delete_associado(cid, aid):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    a = Associado.query.filter_by(id=aid, clube_id=cid).first()
    if not a:
        return err('Associado não encontrado.', 404)
    db.session.delete(a)
    db.session.commit()
    return ok()


# ── USUÁRIOS ────────────────────────────────────────────────────────────────
@api_bp.route('/usuarios')
@login_required
def list_usuarios():
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    q      = request.args.get('q', '').strip()
    perfil = request.args.get('perfil', '').strip()
    query  = Usuario.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Usuario.nome.ilike(like), Usuario.email.ilike(like)
        ))
    if perfil:
        query = query.filter_by(perfil=perfil)
    return ok([usuario_dict(u) for u in query.order_by(Usuario.nome).all()])


@api_bp.route('/usuarios', methods=['POST'])
@login_required
def create_usuario():
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    d     = request.get_json(silent=True) or {}
    nome  = (d.get('nome') or '').strip()
    email = (d.get('email') or '').strip().lower()
    senha = d.get('senha') or ''
    if not nome:
        return err('O nome é obrigatório.')
    if not email or '@' not in email:
        return err('Informe um e-mail válido.')
    if not senha or len(senha) < 6:
        return err('A senha deve ter no mínimo 6 caracteres.')
    if Usuario.query.filter_by(email=email).first():
        return err('Já existe um usuário com este e-mail.')
    u = Usuario(
        nome=nome, email=email,
        senha_hash=generate_password_hash(senha),
        perfil=d.get('perfil', 'operador'),
        ativo=bool(d.get('ativo', True)),
    )
    db.session.add(u)
    db.session.commit()
    return ok(usuario_dict(u), code=201)


@api_bp.route('/usuarios/<int:id>', methods=['PUT'])
@login_required
def update_usuario(id):
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    u = db.session.get(Usuario, id)
    if not u:
        return err('Usuário não encontrado.', 404)
    d     = request.get_json(silent=True) or {}
    nome  = (d.get('nome') or '').strip()
    email = (d.get('email') or '').strip().lower()
    if not nome:
        return err('O nome é obrigatório.')
    if not email or '@' not in email:
        return err('Informe um e-mail válido.')
    if Usuario.query.filter(Usuario.email == email, Usuario.id != id).first():
        return err('E-mail já utilizado por outro usuário.')
    u.nome   = nome
    u.email  = email
    u.perfil = d.get('perfil', u.perfil)
    u.ativo  = bool(d.get('ativo', u.ativo))
    senha = d.get('senha') or ''
    if senha:
        if len(senha) < 6:
            return err('A senha deve ter no mínimo 6 caracteres.')
        u.senha_hash = generate_password_hash(senha)
    db.session.commit()
    return ok(usuario_dict(u))


@api_bp.route('/usuarios/<int:id>', methods=['DELETE'])
@login_required
def delete_usuario(id):
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    if id == current_user.id:
        return err('Você não pode excluir sua própria conta.')
    u = db.session.get(Usuario, id)
    if not u:
        return err('Usuário não encontrado.', 404)
    db.session.delete(u)
    db.session.commit()
    return ok()


# ── WHATSAPP SERVICE PROXY ───────────────────────────────────────────────────
@api_bp.route('/wa/status')
@login_required
def wa_status():
    try:
        r = http.get(f'{WA_SERVICE}/status', timeout=3)
        return ok(r.json())
    except Exception:
        return ok({'status': 'OFFLINE', 'hasQr': False})


@api_bp.route('/wa/qr')
@login_required
def wa_qr():
    try:
        r = http.get(f'{WA_SERVICE}/qr', timeout=3)
        if r.ok:
            return ok(r.json())
        return err('QR não disponível.', 404)
    except Exception as e:
        return err(str(e))


@api_bp.route('/wa/send', methods=['POST'])
@login_required
def wa_send():
    d = request.get_json(silent=True) or {}
    try:
        r = http.post(f'{WA_SERVICE}/send', json={
            'numero':   d.get('numero'),
            'mensagem': d.get('mensagem'),
        }, timeout=15)
        data = r.json()
        if not r.ok:
            return err(data.get('error', 'Erro ao enviar.'))
        log = WaLog(
            clube_nome=d.get('clube', ''),
            mensagem=d.get('mensagem', ''),
            enviado_por_id=current_user.id,
        )
        db.session.add(log)
        db.session.commit()
        return ok()
    except Exception as e:
        return err(str(e))


@api_bp.route('/wa/disconnect', methods=['POST'])
@login_required
def wa_disconnect():
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    try:
        r = http.post(f'{WA_SERVICE}/disconnect', timeout=5)
        return ok(r.json())
    except Exception as e:
        return err(str(e))


# ── GESTÃO: DOCUMENTOS CENTRALIZADOS ─────────────────────────────────────────
@api_bp.route('/gestao/documentos')
@login_required
def list_all_documentos():
    q    = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '').strip()
    query = Documento.query.join(Clube)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            Clube.nome_clube.ilike(like),
            Documento.nome.ilike(like),
        ))
    if tipo:
        query = query.filter(Documento.tipo == tipo)
    docs = query.order_by(Documento.enviado_em.desc()).all()
    return ok([{**documento_dict(d), 'clubeId': d.clube_id,
                'clubeNome': d.clube.nome_clube if d.clube else '—'} for d in docs])


@api_bp.route('/gestao/documentos', methods=['POST'])
@login_required
def upload_gestao_documento():
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    cid = request.form.get('clube_id')
    if not cid:
        return err('Selecione o clube.')
    c = db.session.get(Clube, int(cid))
    if not c:
        return err('Clube não encontrado.', 404)
    if 'file' not in request.files:
        return err('Nenhum arquivo enviado.')
    f = request.files['file']
    if not f.filename:
        return err('Arquivo inválido.')
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return err('Tipo não permitido. Use PDF, DOC, DOCX ou imagens.')
    safe   = secure_filename(f.filename)
    unique = f'{uuid.uuid4().hex}_{safe}'
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique)
    f.save(filepath)
    doc = Documento(
        clube_id=c.id,
        nome=request.form.get('nome') or f.filename,
        tipo=request.form.get('tipo') or 'outro',
        filename=unique,
        tamanho=os.path.getsize(filepath),
        enviado_por_id=current_user.id,
    )
    db.session.add(doc)
    db.session.commit()
    return ok({**documento_dict(doc), 'clubeId': c.id, 'clubeNome': c.nome_clube}, code=201)


# ── TRIMESTRALIDADES ──────────────────────────────────────────────────────────
@api_bp.route('/trimestralidades')
@login_required
def list_trimestralidades():
    ano = request.args.get('ano', datetime.utcnow().year, type=int)
    registros = Trimestralidade.query.filter_by(ano=ano).all()
    return ok([{
        'id':             r.id,
        'clubeId':        r.clube_id,
        'ano':            r.ano,
        'trimestre':      r.trimestre,
        'status':         r.status,
        'valor':          str(r.valor) if r.valor else None,
        'dataVencimento': r.data_vencimento.isoformat() if r.data_vencimento else None,
        'dataPagamento':  r.data_pagamento.isoformat()  if r.data_pagamento  else None,
        'observacoes':    r.observacoes,
        'registradoPor':  r.registrado_por.nome if r.registrado_por else None,
    } for r in registros])


@api_bp.route('/trimestralidades/<int:clube_id>/<int:ano>/<int:trimestre>', methods=['PUT'])
@login_required
def update_trimestralidade(clube_id, ano, trimestre):
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    if trimestre not in (1, 2, 3, 4):
        return err('Trimestre inválido.')
    c = db.session.get(Clube, clube_id)
    if not c:
        return err('Clube não encontrado.', 404)
    r = Trimestralidade.query.filter_by(clube_id=clube_id, ano=ano, trimestre=trimestre).first()
    if not r:
        r = Trimestralidade(clube_id=clube_id, ano=ano, trimestre=trimestre)
        db.session.add(r)
    d = request.get_json(silent=True) or {}
    r.status            = d.get('status', 'pendente')
    r.valor             = d.get('valor') or None
    r.data_vencimento   = parse_date(d.get('dataVencimento'))
    r.data_pagamento    = parse_date(d.get('dataPagamento'))
    r.observacoes       = d.get('observacoes') or None
    r.registrado_por_id = current_user.id
    r.atualizado_em     = datetime.utcnow()
    db.session.commit()
    return ok({'id': r.id, 'clubeId': r.clube_id, 'trimestre': r.trimestre,
               'status': r.status, 'valor': str(r.valor) if r.valor else None,
               'dataPagamento': r.data_pagamento.isoformat() if r.data_pagamento else None})


# ── E-MAIL ───────────────────────────────────────────────────────────────────
_EMAIL_KEYS = ['smtp_host', 'smtp_port', 'smtp_tls', 'smtp_ssl',
               'smtp_usuario', 'smtp_senha', 'email_remetente', 'nome_remetente']


def _cfg_email():
    rows = Config.query.filter(Config.chave.in_(_EMAIL_KEYS)).all()
    return {r.chave: r.valor for r in rows}


def _send_email(to, subject, body, cfg, html_body=None):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    nome = cfg.get('nome_remetente') or 'FBVA'
    rem  = cfg.get('email_remetente') or cfg.get('smtp_usuario', '')
    msg['From'] = f'{nome} <{rem}>'
    msg['To']   = to
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    host    = cfg.get('smtp_host', '')
    port    = int(cfg.get('smtp_port') or 587)
    use_ssl = cfg.get('smtp_ssl') == '1'
    use_tls = cfg.get('smtp_tls', '1') == '1'
    usuario = cfg.get('smtp_usuario', '')
    senha   = cfg.get('smtp_senha', '')
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=15) as s:
            s.login(usuario, senha)
            s.sendmail(rem, to, msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=15) as s:
            if use_tls:
                s.starttls()
            s.login(usuario, senha)
            s.sendmail(rem, to, msg.as_string())


@api_bp.route('/email/config')
@login_required
def get_email_config():
    cfg = _cfg_email()
    safe = {k: v for k, v in cfg.items() if k != 'smtp_senha'}
    safe['smtp_senha']  = '••••••••' if cfg.get('smtp_senha') else ''
    safe['configured']  = bool(cfg.get('smtp_host') and cfg.get('smtp_usuario') and cfg.get('smtp_senha'))
    return ok(safe)


@api_bp.route('/email/config', methods=['POST'])
@login_required
def save_email_config():
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    d = request.get_json(silent=True) or {}
    for key in _EMAIL_KEYS:
        val = d.get(key)
        if key == 'smtp_senha' and val and val.startswith('•'):
            continue
        if val is not None:
            row = db.session.get(Config, key)
            if row:
                row.valor = val
            else:
                db.session.add(Config(chave=key, valor=val))
    db.session.commit()
    return ok()


@api_bp.route('/email/testar', methods=['POST'])
@login_required
def testar_email():
    if not current_user.pode_gerenciar_usuarios():
        return err('Sem permissão.', 403)
    cfg = _cfg_email()
    if not all([cfg.get('smtp_host'), cfg.get('smtp_usuario'), cfg.get('smtp_senha')]):
        return err('Configure host, usuário e senha SMTP antes de testar.')
    try:
        _send_email(
            to=current_user.email,
            subject='Teste FBVA — Configuração de E-mail',
            body=f'Olá {current_user.nome},\n\nA configuração de e-mail do sistema FBVA está funcionando corretamente!',
            cfg=cfg,
        )
        return ok(f'E-mail de teste enviado para {current_user.email}')
    except Exception as e:
        return err(str(e))


@api_bp.route('/email/send', methods=['POST'])
@login_required
def send_emails():
    if not current_user.pode_editar():
        return err('Sem permissão.', 403)
    cfg = _cfg_email()
    if not all([cfg.get('smtp_host'), cfg.get('smtp_usuario'), cfg.get('smtp_senha')]):
        return err('SMTP não configurado. Acesse Mensageiro E-mail → Configurações.')
    d = request.get_json(silent=True) or {}
    destinatarios = d.get('destinatarios', [])
    if not destinatarios:
        return err('Nenhum destinatário informado.')
    resultados = []
    for dest in destinatarios:
        try:
            _send_email(to=dest['email'], subject=dest['assunto'],
                        body=dest['mensagem'], cfg=cfg,
                        html_body=dest.get('mensagem_html'))
            db.session.add(EmailLog(
                clube_nome=dest.get('clube', ''), destinatario=dest['email'],
                assunto=dest['assunto'], mensagem=dest['mensagem'],
                status='ok', enviado_por_id=current_user.id,
            ))
            resultados.append({'clube': dest.get('clube'), 'ok': True})
        except Exception as e:
            db.session.add(EmailLog(
                clube_nome=dest.get('clube', ''), destinatario=dest['email'],
                assunto=dest['assunto'], mensagem=dest['mensagem'],
                status='erro', erro=str(e), enviado_por_id=current_user.id,
            ))
            resultados.append({'clube': dest.get('clube'), 'ok': False, 'erro': str(e)})
    db.session.commit()
    return ok(resultados)


@api_bp.route('/email/log')
@login_required
def get_email_log():
    logs = EmailLog.query.order_by(EmailLog.enviado_em.desc()).limit(200).all()
    return ok([{
        'id':          l.id,
        'clube':       l.clube_nome,
        'destinatario':l.destinatario,
        'assunto':     l.assunto,
        'msg':         l.mensagem,
        'status':      l.status,
        'hora':        l.enviado_em.strftime('%d/%m/%Y %H:%M'),
        'por':         l.enviado_por.nome if l.enviado_por else '—',
    } for l in logs])


@api_bp.route('/email/log', methods=['DELETE'])
@login_required
def clear_email_log():
    EmailLog.query.delete()
    db.session.commit()
    return ok()


# ── WHATSAPP LOG ─────────────────────────────────────────────────────────────
@api_bp.route('/wa-log')
@login_required
def get_wa_log():
    logs = (WaLog.query
            .order_by(WaLog.enviado_em.desc())
            .limit(200).all())
    return ok([{
        'id':    l.id,
        'clube': l.clube_nome,
        'msg':   l.mensagem,
        'hora':  l.enviado_em.strftime('%d/%m/%Y %H:%M'),
        'por':   l.enviado_por.nome if l.enviado_por else '—',
    } for l in logs])


@api_bp.route('/wa-log', methods=['POST'])
@login_required
def add_wa_log():
    d = request.get_json(silent=True) or {}
    log = WaLog(
        clube_nome=d.get('clube', ''),
        mensagem=d.get('msg', ''),
        enviado_por_id=current_user.id,
    )
    db.session.add(log)
    db.session.commit()
    return ok({'id': log.id})


@api_bp.route('/wa-log', methods=['DELETE'])
@login_required
def clear_wa_log():
    WaLog.query.delete()
    db.session.commit()
    return ok()


# ═══════════════════════════════════════════════════════════════════════════════
# CLIPPING DE NOTÍCIAS
# ═══════════════════════════════════════════════════════════════════════════════

CLIPPING_KEYWORDS = [
    'carros antigos',
    'veículos antigos',
    'automóveis clássicos',
    'carros clássicos',
    'veículos históricos',
    'encontro de carros antigos',
    'mostra de carros antigos',
    'colecionadores de carros',
    'FBVA federação brasileira veículos antigos',
]


def _scrape_clipping():
    import xml.etree.ElementTree as ET
    from urllib.parse import quote
    from email.utils import parsedate_to_datetime

    novos = 0
    for kw in CLIPPING_KEYWORDS:
        try:
            url = (
                'https://news.google.com/rss/search?q='
                + quote(f'"{kw}"')
                + '&hl=pt-BR&gl=BR&ceid=BR:pt-419'
            )
            r = http.get(url, timeout=12, headers={'User-Agent': 'Mozilla/5.0'})
            root = ET.fromstring(r.content)
            for item in root.findall('.//item'):
                titulo = (item.findtext('title') or '').strip()
                link   = (item.findtext('link')  or '').strip()
                desc   = (item.findtext('description') or '').strip()
                fonte_el = item.find('source')
                fonte  = (fonte_el.text or '').strip() if fonte_el is not None else ''
                pub    = (item.findtext('pubDate') or '').strip()
                try:
                    pub_dt = parsedate_to_datetime(pub).replace(tzinfo=None) if pub else None
                except Exception:
                    pub_dt = None
                if not titulo or not link:
                    continue
                if not ClippingNoticia.query.filter_by(url=link).first():
                    db.session.add(ClippingNoticia(
                        titulo=titulo[:500],
                        url=link[:1000],
                        fonte=fonte[:200],
                        resumo=desc[:1000],
                        publicado_em=pub_dt,
                        palavra_chave=kw,
                    ))
                    novos += 1
        except Exception:
            continue

    db.session.commit()
    cfg = db.session.get(Config, 'clipping_ultima_busca') or Config(chave='clipping_ultima_busca')
    cfg.valor = datetime.utcnow().isoformat()
    db.session.merge(cfg)
    db.session.commit()
    return novos


@api_bp.route('/clipping')
@login_required
def list_clipping():
    nao_lidas = request.args.get('nao_lidas') == '1'
    q = ClippingNoticia.query.order_by(
        ClippingNoticia.publicado_em.desc(),
        ClippingNoticia.coletado_em.desc()
    )
    if nao_lidas:
        q = q.filter_by(lida=False)
    noticias = q.limit(200).all()
    ultima = db.session.get(Config, 'clipping_ultima_busca')
    return ok({
        'noticias': [{
            'id':          n.id,
            'titulo':      n.titulo,
            'url':         n.url,
            'fonte':       n.fonte,
            'resumo':      n.resumo,
            'publicadoEm': n.publicado_em.isoformat() if n.publicado_em else None,
            'coletadoEm':  n.coletado_em.isoformat() if n.coletado_em else None,
            'palavraChave': n.palavra_chave,
            'lida':        n.lida,
        } for n in noticias],
        'ultimaBusca': ultima.valor if ultima else None,
        'total': ClippingNoticia.query.count(),
        'naoLidas': ClippingNoticia.query.filter_by(lida=False).count(),
    })


@api_bp.route('/clipping/buscar', methods=['POST'])
@login_required
def buscar_clipping():
    novos = _scrape_clipping()
    return ok({'novos': novos})


@api_bp.route('/clipping/<int:nid>/lida', methods=['PATCH'])
@login_required
def marcar_lida_clipping(nid):
    n = db.session.get(ClippingNoticia, nid)
    if not n:
        return err('Notícia não encontrada.', 404)
    n.lida = request.json.get('lida', True)
    db.session.commit()
    return ok()


@api_bp.route('/clipping/lidas-todas', methods=['PATCH'])
@login_required
def marcar_todas_lidas():
    ClippingNoticia.query.filter_by(lida=False).update({'lida': True})
    db.session.commit()
    return ok()


@api_bp.route('/clipping/<int:nid>', methods=['DELETE'])
@login_required
def deletar_clipping(nid):
    n = db.session.get(ClippingNoticia, nid)
    if not n:
        return err('Notícia não encontrada.', 404)
    db.session.delete(n)
    db.session.commit()
    return ok()


@api_bp.route('/clipping', methods=['DELETE'])
@login_required
def limpar_clipping():
    ClippingNoticia.query.delete()
    db.session.commit()
    return ok()
