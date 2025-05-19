import pool from '../utils/db.js';
import { hashPassword, validatePassword } from '../utils/auth.js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Adjust path to point to backend/.env
dotenv.config({ path: path.join(__dirname, '../../backend/.env') });

async function createAdminUser() {
  let connection;
  try {
    const adminPassword = process.env.ADMIN_PASSWORD;
    const adminUsername = process.env.ADMIN_USERNAME;

    if (!adminUsername || !adminPassword) {
      throw new Error('ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env file');
    }

    if (!validatePassword(adminPassword)) {
      throw new Error(
        'Password does not meet security requirements.\n' +
        'Password must:\n' +
        '- Be at least 8 characters long\n' +
        '- Contain at least one uppercase letter\n' +
        '- Contain at least one lowercase letter\n' +
        '- Contain at least one number\n' +
        '- Contain at least one special character (!@#$%^&*(),.?":{}|<>)'
      );
    }

    connection = await pool.getConnection();

    const [existingUser] = await connection.execute(
      'SELECT * FROM users WHERE username = ?',
      [adminUsername]
    );

    if (existingUser.length > 0) {
      throw new Error('Admin user already exists');
    }

    const hashedPassword = await hashPassword(adminPassword);
    await connection.execute(
      'INSERT INTO users (username, password) VALUES (?, ?)',
      [adminUsername, hashedPassword]
    );

    console.log('Admin user created successfully');
  } catch (error) {
    console.error('Error creating admin user:', error.message);
  } finally {
    if (connection) {
      connection.release();
    }
    process.exit();
  }
}

createAdminUser();