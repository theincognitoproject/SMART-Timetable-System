import pool from '../utils/db';
import { comparePassword } from '../utils/auth.js';

export const loginUser = async (username, password) => {
  let connection;
  try {
    connection = await pool.getConnection();
    
    const [rows] = await connection.execute(
      'SELECT * FROM users WHERE username = ?',
      [username]
    );

    if (rows.length === 0) {
      throw new Error('Invalid credentials');
    }

    const user = rows[0];
    const isValidPassword = await comparePassword(password, user.password);

    if (!isValidPassword) {
      throw new Error('Invalid credentials');
    }

    return { success: true, message: 'Login successful' };
  } catch (error) {
    throw error;
  } finally {
    if (connection) connection.release();
  }
};