const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode  = require('qrcode');

const app  = express();
const PORT = process.env.WA_PORT || 3001;
app.use(express.json());

// ── Estado ───────────────────────────────────────────
let qrBase64  = null;
let status    = 'INITIALIZING'; // INITIALIZING | QR_READY | CONNECTED | DISCONNECTED

// ── Cliente WhatsApp ─────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './wa_session' }),
    puppeteer: {
        executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu',
               '--disable-dev-shm-usage', '--disable-extensions'],
    },
});

client.on('qr', async (qr) => {
    console.log('[WA] QR Code gerado — escaneie pelo WhatsApp.');
    qrBase64 = await qrcode.toDataURL(qr);
    status   = 'QR_READY';
});

client.on('authenticated', () => {
    console.log('[WA] Autenticado.');
    qrBase64 = null;
    status   = 'CONNECTED';
});

client.on('ready', () => {
    console.log('[WA] Pronto para enviar mensagens.');
    status   = 'CONNECTED';
    qrBase64 = null;
});

client.on('auth_failure', (msg) => {
    console.error('[WA] Falha na autenticação:', msg);
    status = 'DISCONNECTED';
});

client.on('disconnected', (reason) => {
    console.log('[WA] Desconectado:', reason);
    status   = 'DISCONNECTED';
    qrBase64 = null;
});

client.initialize().catch(e => {
    console.error('[WA] Erro ao inicializar:', e.message);
    status = 'DISCONNECTED';
});

// ── Helpers ──────────────────────────────────────────
function formatNumber(num) {
    const d = (num || '').replace(/\D/g, '');
    if (d.startsWith('55') && d.length >= 12) return d + '@c.us';
    return '55' + d + '@c.us';
}

// ── Rotas ────────────────────────────────────────────
app.get('/status', (req, res) => {
    res.json({ status, hasQr: !!qrBase64 });
});

app.get('/qr', (req, res) => {
    if (!qrBase64) return res.status(404).json({ error: 'QR não disponível.' });
    res.json({ qr: qrBase64 });
});

app.post('/send', async (req, res) => {
    if (status !== 'CONNECTED') {
        return res.status(503).json({ error: 'WhatsApp não conectado.' });
    }
    const { numero, mensagem } = req.body || {};
    if (!numero || !mensagem) {
        return res.status(400).json({ error: 'numero e mensagem são obrigatórios.' });
    }
    try {
        const chatId = formatNumber(numero);
        await client.sendMessage(chatId, mensagem);
        res.json({ ok: true });
    } catch (e) {
        console.error('[WA] Erro ao enviar:', e.message);
        res.status(500).json({ error: e.message });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        await client.logout();
        status   = 'DISCONNECTED';
        qrBase64 = null;
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.listen(PORT, () => {
    console.log(`[WA] Serviço rodando em http://localhost:${PORT}`);
    console.log('[WA] Aguardando inicialização do WhatsApp...');
});
