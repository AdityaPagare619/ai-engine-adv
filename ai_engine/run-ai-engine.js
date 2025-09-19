#!/usr/bin/env node

// Simple AI Engine runner - bypasses TypeScript compilation
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

console.log('🚀 Starting AI Engine Quick Runner...');
console.log('📍 Current Directory:', process.cwd());
console.log('🏗️  Architecture: RPC-based with PostgreSQL functions');

// Check if PostgreSQL connection string exists
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
    console.log('✅ Environment file found');
    const envContent = fs.readFileSync(envPath, 'utf8');
    if (envContent.includes('DATABASE_URL=')) {
        console.log('✅ Database URL configured');
    } else {
        console.log('⚠️  Database URL not found in .env');
    }
} else {
    console.log('⚠️  .env file not found');
}

// Show project structure
console.log('\n📁 Project Structure:');
try {
    const srcPath = path.join(__dirname, 'src');
    if (fs.existsSync(srcPath)) {
        const files = fs.readdirSync(srcPath);
        files.forEach(file => {
            console.log(`   📄 src/${file}`);
        });
        
        // Check services
        const servicesPath = path.join(srcPath, 'services');
        if (fs.existsSync(servicesPath)) {
            const serviceFiles = fs.readdirSync(servicesPath);
            console.log('   🔧 Services:');
            serviceFiles.forEach(file => {
                console.log(`      - ${file}`);
            });
        }
        
        // Check schema
        const schemaPath = path.join(srcPath, 'schema');
        if (fs.existsSync(schemaPath)) {
            const schemaFiles = fs.readdirSync(schemaPath);
            console.log('   🗄️  Schema Files:');
            schemaFiles.forEach(file => {
                console.log(`      - ${file}`);
            });
        }
    }
} catch (error) {
    console.log('   ❌ Error reading project structure:', error.message);
}

// Try to install and run
console.log('\n🔄 Attempting to start AI Engine...');

const installCommands = [
    'node -e "console.log(\'Node.js version:\', process.version)"',
    // Try different installation methods
    'where npm',
    'npm --version'
];

function runCommand(command) {
    return new Promise((resolve, reject) => {
        console.log(`⚡ Running: ${command}`);
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.log(`❌ Error: ${error.message}`);
                resolve(false);
            } else {
                console.log(`✅ Output: ${stdout.trim()}`);
                if (stderr) console.log(`⚠️  Stderr: ${stderr.trim()}`);
                resolve(true);
            }
        });
    });
}

async function main() {
    console.log('\n🧪 Testing Node.js environment...');
    
    // Test basic Node.js
    const nodeTest = await runCommand('node --version');
    if (!nodeTest) {
        console.log('❌ Node.js not available');
        return;
    }
    
    // Test npm
    const npmTest = await runCommand('npm --version');
    if (npmTest) {
        console.log('✅ npm is available, trying to install dependencies...');
        
        // Try to install dependencies
        const installResult = await runCommand('npm install --no-optional --legacy-peer-deps');
        if (installResult) {
            console.log('✅ Dependencies installed successfully!');
            console.log('🚀 Starting AI Engine with npm...');
            
            // Try to run with ts-node
            exec('npx ts-node src/index.ts', (error, stdout, stderr) => {
                if (error) {
                    console.log('❌ TypeScript execution failed:', error.message);
                    console.log('📝 You can now manually run: npx ts-node src/index.ts');
                } else {
                    console.log('✅ AI Engine started successfully!');
                    console.log(stdout);
                }
                if (stderr) console.log('⚠️  Stderr:', stderr);
            });
        } else {
            console.log('❌ Failed to install dependencies via npm');
            showManualInstructions();
        }
    } else {
        console.log('❌ npm not available');
        showManualInstructions();
    }
}

function showManualInstructions() {
    console.log('\n📋 Manual Instructions:');
    console.log('');
    console.log('1. Install dependencies globally:');
    console.log('   npm install -g typescript ts-node @types/node');
    console.log('');
    console.log('2. Install project dependencies:');
    console.log('   npm install express cors helmet morgan winston pg @types/express @types/cors @types/morgan @types/pg dotenv');
    console.log('');
    console.log('3. Start the AI Engine:');
    console.log('   npx ts-node src/index.ts');
    console.log('');
    console.log('4. Alternative - compile and run:');
    console.log('   npx tsc');
    console.log('   node dist/index.js');
    console.log('');
    console.log('5. Test endpoints:');
    console.log('   curl http://localhost:8005/health');
    console.log('');
    console.log('🔗 API Endpoints:');
    console.log('   GET  /health                 - Health check');
    console.log('   POST /api/ai/trace          - Knowledge tracing (BKT)');
    console.log('   POST /api/ai/recommend      - Get recommendations');
    console.log('   POST /api/ai/predict        - Score prediction');
    console.log('');
    console.log('📊 Database Requirements:');
    console.log('   - PostgreSQL with your existing JEE Smart AI Platform database');
    console.log('   - Run schema migrations from src/schema/ directory');
    console.log('   - Ensure RPC functions are created (07_functions.sql)');
    console.log('');
    console.log('🔍 Troubleshooting:');
    console.log('   - Check DATABASE_URL in .env file');
    console.log('   - Verify PostgreSQL is running');
    console.log('   - Ensure port 8005 is available');
}

// Start the process
main().catch(console.error);

// Keep process alive to show instructions
process.on('SIGINT', () => {
    console.log('\n👋 AI Engine setup helper terminated');
    process.exit(0);
});