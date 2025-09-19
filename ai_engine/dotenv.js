// Simple dotenv mock
const fs = require('fs');

module.exports = {
  config: function() {
    if (fs.existsSync('.env')) {
      const content = fs.readFileSync('.env', 'utf8');
      content.split('\n').forEach(line => {
        line = line.trim();
        if (line && !line.startsWith('#')) {
          const equalIndex = line.indexOf('=');
          if (equalIndex > 0) {
            const key = line.substring(0, equalIndex).trim();
            const value = line.substring(equalIndex + 1).trim();
            process.env[key] = value;
          }
        }
      });
    }
  }
};