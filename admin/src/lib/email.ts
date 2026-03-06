import { Resend } from 'resend';

// Lazy-initialize Resend (env vars not available at build time)
let _resend: Resend | null = null;
function getResend() {
  if (!_resend) {
    _resend = new Resend(process.env.RESEND_API_KEY);
  }
  return _resend;
}

const FROM_EMAIL = process.env.EMAIL_FROM || 'noreply@kingshort.app';
const APP_NAME = 'KingShortID';

interface EmailOptions {
  to: string | string[];
  subject: string;
  html: string;
  text?: string;
}

/**
 * Send email using Resend
 */
export async function sendEmail({ to, subject, html, text }: EmailOptions) {
  try {
    const data = await getResend().emails.send({
      from: `${APP_NAME} <${FROM_EMAIL}>`,
      to: Array.isArray(to) ? to : [to],
      subject,
      html,
      text,
    });

    console.log('Email sent successfully:', data.id);
    return { success: true, id: data.id };
  } catch (error: any) {
    console.error('Failed to send email:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Send welcome email to new user
 */
export async function sendWelcomeEmail(email: string, name: string) {
  const subject = `Welcome to ${APP_NAME}! 🎬`;

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #FF8C00 0%, #FFD700 100%); padding: 40px 20px; text-align: center; }
        .header h1 { color: white; margin: 0; font-size: 32px; }
        .content { padding: 40px 30px; }
        .content h2 { color: #333; margin-top: 0; }
        .content p { color: #666; line-height: 1.6; }
        .button { display: inline-block; background: #FF8C00; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
        .features { margin: 30px 0; }
        .feature { padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0; }
        .feature h3 { margin: 0 0 8px 0; color: #FF8C00; font-size: 16px; }
        .feature p { margin: 0; color: #666; font-size: 14px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🎬 Welcome to ${APP_NAME}!</h1>
        </div>
        <div class="content">
          <h2>Hi ${name},</h2>
          <p>We're excited to have you join our community of drama lovers! Get ready to discover amazing short dramas from around the world.</p>
          
          <a href="https://kingshort.app/discover" class="button">Start Watching Now →</a>
          
          <div class="features">
            <div class="feature">
              <h3>🎰 Daily Spin Wheel</h3>
              <p>Spin daily to earn free coins and unlock premium content</p>
            </div>
            <div class="feature">
              <h3>🏆 Achievements</h3>
              <p>Complete challenges and earn rewards as you watch</p>
            </div>
            <div class="feature">
              <h3>✨ AI Recommendations</h3>
              <p>Get personalized drama suggestions based on your taste</p>
            </div>
            <div class="feature">
              <h3>📥 Offline Downloads</h3>
              <p>Download episodes and watch anytime, anywhere</p>
            </div>
          </div>
          
          <p>Need help getting started? Check out our <a href="https://kingshort.app/help" style="color: #FF8C00;">Help Center</a> or reply to this email.</p>
          
          <p>Happy watching!<br>The ${APP_NAME} Team</p>
        </div>
        <div class="footer">
          <p>© ${new Date().getFullYear()} ${APP_NAME}. All rights reserved.</p>
          <p>You're receiving this email because you signed up for ${APP_NAME}.</p>
        </div>
      </div>
    </body>
    </html>
  `;

  return sendEmail({ to: email, subject, html });
}

/**
 * Send new episode notification
 */
export async function sendNewEpisodeEmail(
  email: string,
  dramaTitle: string,
  episodeNumber: number,
  episodeTitle: string
) {
  const subject = `New Episode: ${dramaTitle} - Episode ${episodeNumber}`;

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #FF8C00 0%, #FFD700 100%); padding: 30px 20px; text-align: center; }
        .header h1 { color: white; margin: 0; font-size: 24px; }
        .content { padding: 30px; }
        .episode-card { background: #f8f9fa; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #FF8C00; }
        .episode-card h2 { margin: 0 0 10px 0; color: #333; font-size: 20px; }
        .episode-card p { margin: 5px 0; color: #666; }
        .button { display: inline-block; background: #FF8C00; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🎬 New Episode Available!</h1>
        </div>
        <div class="content">
          <p>Great news! A new episode is ready for you to watch:</p>
          
          <div class="episode-card">
            <h2>${dramaTitle}</h2>
            <p><strong>Episode ${episodeNumber}:</strong> ${episodeTitle}</p>
            <p style="color: #FF8C00; font-weight: 600; margin-top: 10px;">🆕 Now Streaming</p>
          </div>
          
          <a href="https://kingshort.app/player?episode=${episodeNumber}" class="button">Watch Now →</a>
          
          <p style="color: #999; font-size: 14px; margin-top: 30px;">
            Don't want these notifications? <a href="https://kingshort.app/settings/notifications" style="color: #FF8C00;">Manage preferences</a>
          </p>
        </div>
        <div class="footer">
          <p>© ${new Date().getFullYear()} ${APP_NAME}. All rights reserved.</p>
        </div>
      </div>
    </body>
    </html>
  `;

  return sendEmail({ to: email, subject, html });
}

/**
 * Send weekly digest email
 */
export async function sendWeeklyDigestEmail(
  email: string,
  name: string,
  stats: {
    episodesWatched: number;
    coinsEarned: number;
    newDramas: Array<{ title: string; cover: string }>;
  }
) {
  const subject = `Your Weekly ${APP_NAME} Digest 📊`;

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #FF8C00 0%, #FFD700 100%); padding: 30px 20px; text-align: center; }
        .header h1 { color: white; margin: 0; font-size: 24px; }
        .content { padding: 30px; }
        .stats { display: flex; justify-content: space-around; margin: 30px 0; }
        .stat { text-align: center; }
        .stat-value { font-size: 32px; font-weight: bold; color: #FF8C00; }
        .stat-label { color: #666; font-size: 14px; margin-top: 5px; }
        .drama-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
        .drama-item { text-align: center; }
        .drama-item img { width: 100%; border-radius: 8px; }
        .drama-item p { margin: 8px 0 0 0; font-size: 14px; color: #333; }
        .button { display: inline-block; background: #FF8C00; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📊 Your Weekly Digest</h1>
        </div>
        <div class="content">
          <h2>Hi ${name},</h2>
          <p>Here's what you accomplished this week:</p>
          
          <div class="stats">
            <div class="stat">
              <div class="stat-value">${stats.episodesWatched}</div>
              <div class="stat-label">Episodes Watched</div>
            </div>
            <div class="stat">
              <div class="stat-value">${stats.coinsEarned}</div>
              <div class="stat-label">Coins Earned</div>
            </div>
          </div>
          
          <h3>🆕 New Dramas This Week</h3>
          <div class="drama-grid">
            ${stats.newDramas.map(drama => `
              <div class="drama-item">
                <img src="${drama.cover}" alt="${drama.title}" />
                <p>${drama.title}</p>
              </div>
            `).join('')}
          </div>
          
          <a href="https://kingshort.app/discover" class="button">Discover More →</a>
        </div>
        <div class="footer">
          <p>© ${new Date().getFullYear()} ${APP_NAME}. All rights reserved.</p>
          <p><a href="https://kingshort.app/settings/notifications" style="color: #FF8C00;">Manage email preferences</a></p>
        </div>
      </div>
    </body>
    </html>
  `;

  return sendEmail({ to: email, subject, html });
}

/**
 * Send password reset email
 */
export async function sendPasswordResetEmail(
  email: string,
  resetToken: string
) {
  const subject = 'Reset Your Password';
  const resetLink = `https://kingshort.app/reset-password?token=${resetToken}`;

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: #333; padding: 30px 20px; text-align: center; }
        .header h1 { color: white; margin: 0; font-size: 24px; }
        .content { padding: 30px; }
        .content p { color: #666; line-height: 1.6; }
        .button { display: inline-block; background: #FF8C00; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🔐 Reset Your Password</h1>
        </div>
        <div class="content">
          <p>We received a request to reset your password. Click the button below to create a new password:</p>
          
          <a href="${resetLink}" class="button">Reset Password →</a>
          
          <div class="warning">
            <p style="margin: 0; color: #856404;"><strong>⚠️ Security Notice:</strong> This link will expire in 1 hour. If you didn't request this, please ignore this email and your password will remain unchanged.</p>
          </div>
          
          <p style="color: #999; font-size: 14px;">If the button doesn't work, copy and paste this link into your browser:</p>
          <p style="color: #999; font-size: 12px; word-break: break-all;">${resetLink}</p>
        </div>
        <div class="footer">
          <p>© ${new Date().getFullYear()} ${APP_NAME}. All rights reserved.</p>
        </div>
      </div>
    </body>
    </html>
  `;

  return sendEmail({ to: email, subject, html });
}

export default {
  sendEmail,
  sendWelcomeEmail,
  sendNewEpisodeEmail,
  sendWeeklyDigestEmail,
  sendPasswordResetEmail,
};
