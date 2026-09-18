require('dotenv').config();
const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

const ZKBIO_API_URL = process.env.ZKBIO_API_URL || 'http://localhost:8098/api';
const CLOUD_API_URL = process.env.CLOUD_API_URL || 'https://api.fitme.com';
const ZKBIO_TOKEN = process.env.ZKBIO_TOKEN;

let lastPunchCache = {}; // In-memory cache for anti-tailgating

// 1. PUSH: Receive webhook from Cloud (Django) and push to local ZKBio
app.post('/api/zkbio/webhook/sync', async (req, res) => {
    const { user_id, username, is_active, pin } = req.body;
    
    if (!pin) {
        return res.status(400).send({ error: 'PIN is required' });
    }
    
    try {
        if (is_active) {
            // Push user to hardware
            await axios.post(`${ZKBIO_API_URL}/person/add`, {
                pin: pin,
                name: username,
                acc_group_id: 1 // Default access group
            }, { headers: { Authorization: `Token ${ZKBIO_TOKEN}` } });
            console.log(`[SYNC] Added/Updated user ${username} to ZKBio.`);
        } else {
            // Revoke user from hardware
            await axios.post(`${ZKBIO_API_URL}/person/delete`, {
                pin: pin
            }, { headers: { Authorization: `Token ${ZKBIO_TOKEN}` } });
            console.log(`[SYNC] Revoked user ${username} from ZKBio.`);
        }
        res.status(200).send({ success: true });
    } catch (error) {
        console.error(`[SYNC ERROR]`, error.message);
        res.status(500).send({ error: 'Failed to sync with hardware' });
    }
});

// 2. PULL: Receive real-time punch from ZKBio hardware and forward to Cloud
app.post('/api/local/punch', async (req, res) => {
    const { pin, punch_time, terminal_id } = req.body;
    
    // Anti-tailgating: 60 seconds cooldown
    const now = new Date().getTime();
    if (lastPunchCache[pin] && (now - lastPunchCache[pin]) < 60000) {
        console.log(`[TAILGATING] Ignored punch for PIN ${pin}`);
        return res.status(429).send({ error: 'Cooldown active' });
    }
    
    lastPunchCache[pin] = now;
    
    try {
        // Forward to Cloud API
        await axios.post(`${CLOUD_API_URL}/api/punches/log/`, {
            pin,
            punch_time,
            terminal_id
        });
        console.log(`[PUNCH] Forwarded punch for PIN ${pin} to cloud.`);
        res.status(200).send({ success: true });
    } catch (error) {
        console.error(`[PUNCH ERROR] Failed to send to cloud:`, error.message);
        // Implement local queue/retry logic here in a real production app
        res.status(500).send({ error: 'Cloud sync failed' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`[Fit Me] ZKBio Bridge Daemon running on port ${PORT}`);
});
