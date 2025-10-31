// Minimal Node.js server to serve base.html and static assets
const path = require('path');
const express = require('express');

const app = express();
const PORT = process.env.PORT || 5174;

// Serve static assets under /static like Flask
app.use('/static', express.static(path.join(__dirname, '..', 'backend', 'static')));

// Also allow serving any other public assets if needed
app.use('/public', express.static(path.join(__dirname, '..', 'frontend', 'public')));

// Root: serve the Flask template as a static HTML file
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'backend', 'templates', 'base.html'));
});

app.listen(PORT, () => {
  console.log(`Flipbook dev server running at http://localhost:${PORT}`);
});

