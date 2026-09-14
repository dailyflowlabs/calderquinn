const express = require('express');
const path = require('path');
const fs = require('fs');
const cors = require('cors');
const dotenv = require('dotenv');

// Load environment variables (.env.local, then .env if present)
if (fs.existsSync(path.join(__dirname, '.env.local'))) {
  dotenv.config({ path: path.join(__dirname, '.env.local') });
} else {
  dotenv.config();
}

const Stripe = require('stripe');
const stripe = process.env.STRIPE_SECRET_KEY ? new Stripe(process.env.STRIPE_SECRET_KEY) : null;
const PRINTIFY_TOKEN = process.env.PRINTIFY_TOKEN;
const PRINTIFY_SHOP_ID = process.env.PRINTIFY_SHOP_ID || '';

const app = express();
const PORT = process.env.PORT || 3002;

app.use(cors());
app.use(express.json());

// API: Tracks
app.get('/api/tracks', (req, res) => {
  const filePath = path.join(__dirname, 'data', 'tracks.json');
  if (fs.existsSync(filePath)) {
    return res.json(JSON.parse(fs.readFileSync(filePath, 'utf-8')));
  }
  res.json([]);
});

// API: Merch Products
app.get('/api/merch/products', (req, res) => {
  const filePath = path.join(__dirname, 'data', 'products.json');
  if (fs.existsSync(filePath)) {
    return res.json(JSON.parse(fs.readFileSync(filePath, 'utf-8')));
  }
  res.json([]);
});

// API: Merch Checkout (Stripe Checkout Session)
app.post('/api/merch/checkout', async (req, res) => {
  try {
    const { productId, variantId, quantity = 1 } = req.body;

    if (!stripe) {
      return res.status(503).json({ error: 'Checkout is currently in preview mode. Stripe is not yet configured.' });
    }

    if (!productId || !variantId) {
      return res.status(400).json({ error: 'Missing productId or variantId' });
    }

    const filePath = path.join(__dirname, 'data', 'products.json');
    const products = fs.existsSync(filePath) ? JSON.parse(fs.readFileSync(filePath, 'utf-8')) : [];
    const product = products.find(p => p.id === productId);
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const variant = product.variants.find(v => String(v.id) === String(variantId));
    if (!variant) {
      return res.status(404).json({ error: 'Variant not found' });
    }

    const protocol = req.headers['x-forwarded-proto'] || req.protocol || 'https';
    const host = req.headers['host'];
    const origin = `${protocol}://${host}`;

    const displayImage = product.images && product.images.length > 0
      ? (product.images[0].src.startsWith('http') ? product.images[0].src : `${origin}/${product.images[0].src}`)
      : '';

    const unitAmount = Number(variant.price);

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      billing_address_collection: 'required',
      shipping_address_collection: {
        allowed_countries: ['US', 'CA', 'GB', 'IE', 'AU', 'NZ', 'DE', 'FR'],
      },
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `${product.title} - ${variant.title || 'Standard'}`,
              description: product.description ? product.description.substring(0, 250) : 'Official Calder Quinn Merchandise',
              images: displayImage ? [displayImage] : [],
            },
            unit_amount: unitAmount,
          },
          quantity: Number(quantity) || 1,
        },
      ],
      mode: 'payment',
      metadata: {
        productId: product.id,
        variantId: String(variant.id),
        productTitle: product.title,
        variantTitle: variant.title || 'Standard',
        quantity: String(quantity || 1),
      },
      success_url: `${origin}/merch/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/#merch`,
    });

    res.json({ url: session.url });
  } catch (error) {
    console.error('Stripe checkout error:', error);
    res.status(500).json({ error: error.message || 'Failed to create checkout session' });
  }
});

// API: Newsletter / Fan Club Signup
app.post('/api/newsletter', (req, res) => {
  const { email, name } = req.body;
  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'Valid email is required.' });
  }
  console.log(`[The Hollow Fan Club Signup] Email: ${email}, Name: ${name || 'Fan'}`);
  res.json({ success: true, message: "Welcome to The Hollow Fan Club! You're on the insider list." });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Bio Link & Listen Route
app.get(['/listen', '/links', '/bio'], (req, res) => {
  res.redirect('/#music');
});

// Serve static assets
app.use('/music', express.static(path.join(__dirname, 'music')));
app.use('/videos', express.static(path.join(__dirname, 'videos')));
app.use('/images', express.static(path.join(__dirname, 'images')));
app.use('/css', express.static(path.join(__dirname, 'css')));
app.use('/js', express.static(path.join(__dirname, 'js')));
app.use('/data', express.static(path.join(__dirname, 'data')));
app.use(express.static(path.join(__dirname)));

// Fallback to index.html for single page navigation
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[🚀] Calder Quinn official site running on http://localhost:${PORT}`);
});
