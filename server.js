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
const PRINTIFY_SHOP_ID = process.env.PRINTIFY_SHOP_ID || '28933843';

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

// API: Fulfill Merch Order (Stripe -> Printify Order Submission)
app.post('/api/merch/order', async (req, res) => {
  try {
    const { sessionId } = req.body;
    if (!sessionId) {
      return res.status(400).json({ error: 'Missing sessionId' });
    }

    if (!stripe) {
      return res.status(500).json({ error: 'Stripe is not configured' });
    }

    // 1. Fetch checkout session from Stripe
    const session = await stripe.checkout.sessions.retrieve(sessionId);

    if (session.payment_status !== 'paid') {
      return res.status(400).json({ error: 'Session payment has not completed' });
    }

    const { productId, variantId, quantity = '1', productTitle, variantTitle } = session.metadata || {};

    if (!productId || !variantId) {
      return res.status(400).json({ error: 'Session metadata is missing product details' });
    }

    // 2. Parse shipping address details
    const shipping = session.shipping_details || session.collected_information?.shipping_details || session.customer_details;
    if (!shipping || !shipping.address) {
      return res.status(400).json({ error: 'No shipping address provided' });
    }

    const name = shipping.name || 'Customer';
    const nameParts = name.trim().split(/\s+/);
    const firstName = nameParts[0] || 'Customer';
    const lastName = nameParts.slice(1).join(' ') || ' ';

    const address = shipping.address;
    const email = session.customer_details?.email || '';
    const phone = session.customer_details?.phone || '0000000000';

    // 3. Assemble Printify order payload
    const orderPayload = {
      external_id: session.id, // Prevent duplicate orders
      label: `Calder Quinn Order - ${session.id.substring(0, 10)}`,
      line_items: [
        {
          product_id: productId,
          variant_id: Number(variantId),
          quantity: Number(quantity),
        },
      ],
      shipping_method: 1, // Standard shipping
      send_shipping_notification: true,
      address_to: {
        first_name: firstName,
        last_name: lastName,
        email: email,
        phone: phone,
        address1: address.line1,
        address2: address.line2 || '',
        city: address.city,
        region: address.state || '',
        zip: address.postal_code,
        country: address.country,
      },
    };

    console.log(`Submitting order to Printify shop ${PRINTIFY_SHOP_ID} for session ${session.id}...`);

    // 4. Send order request to Printify API
    const printifyResponse = await fetch(`https://api.printify.com/v1/shops/${PRINTIFY_SHOP_ID}/orders.json`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${PRINTIFY_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(orderPayload),
    });

    if (!printifyResponse.ok) {
      const errorText = await printifyResponse.text();
      console.error(`Printify order submission error: ${printifyResponse.status}`, errorText);

      // If already submitted (external_id exists), return success
      if (errorText.includes('already exists') || printifyResponse.status === 409) {
        return res.json({
          success: true,
          message: 'Order was already submitted to Printify',
          productTitle,
          variantTitle,
          quantity,
          email,
          shipping,
        });
      }

      return res.status(502).json({ error: 'Failed to submit order to Printify', details: errorText });
    }

    const printifyData = await printifyResponse.json();
    console.log('Order created successfully on Printify:', printifyData.id);

    return res.json({
      success: true,
      orderId: printifyData.id,
      productTitle,
      variantTitle,
      quantity,
      email,
      shipping,
    });
  } catch (error) {
    console.error('Order fulfillment error:', error);
    res.status(500).json({ error: error.message || 'Error fulfilling order' });
  }
});

// Explicit route for /merch/success
app.get('/merch/success', (req, res) => {
  const successFile = path.join(__dirname, 'merch', 'success', 'index.html');
  if (fs.existsSync(successFile)) {
    return res.sendFile(successFile);
  }
  res.redirect('/#merch');
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
