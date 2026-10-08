from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default="New Chat")
    chat_type = db.Column(db.String(20), nullable=False)  # 'sanskrit' or 'gita'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if message is from user, False if from AI
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)

# Initialize AI client
def get_ai_client():
    api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
    
    if not api_key or not endpoint_id:
        logger.warning("Missing API key or endpoint ID. Using mock AI client.")
        return MockAIClient()
    
    try:
        return OpenAI(
            api_key=api_key,
            base_url=f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1",
        )
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        return MockAIClient()

# Mock AI client for testing or when API is not available
class MockAIClient:
    class ChatCompletions:
        class Create:
            def __init__(self, choices):
                self.choices = choices
        
        def create(self, model, messages, temperature, max_tokens):
            class Choice:
                class Message:
                    def __init__(self, content):
                        self.content = content
                
                def __init__(self, content):
                    self.message = self.Message(content)
            
            mock_response = "I'm a mock AI response. The actual AI service is not available or configured."
            choices = [Choice(mock_response)]
            return self.Create(choices)
    
    def __init__(self):
        self.chat = self.ChatCompletions()

# Ensure database exists
def init_db():
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # Try to diagnose the issue
        try:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                logger.info(f"Database file exists at {db_path}")
                # Try to open the database directly
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"Existing tables: {tables}")
                conn.close()
            else:
                logger.error(f"Database file does not exist at {db_path}")
                # Try to create the directory if it doesn't exist
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
        except Exception as inner_e:
            logger.error(f"Error diagnosing database issue: {inner_e}")

# Initialize database
init_db()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            age = request.form.get('age')
            gender = request.form.get('gender')
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.')
                return redirect(url_for('register'))
            
            # Create new user
            hashed_password = generate_password_hash(password)
            new_user = User(name=name, age=age, gender=gender, username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {e}")
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.')
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash('An error occurred during login. Please try again.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/chat/<chat_type>')
def chat_page(chat_type):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if chat_type not in ['sanskrit', 'gita']:
        return redirect(url_for('dashboard'))
    
    try:
        user_id = session.get('user_id')
        chats = Chat.query.filter_by(user_id=user_id, chat_type=chat_type).order_by(Chat.created_at.desc()).all()
        
        chat_id = request.args.get('chat_id')
        current_chat = None
        messages = []
        
        if chat_id:
            current_chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
            if current_chat:
                messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.timestamp).all()
        
        chat_title = "Sanskrit Phrases" if chat_type == "sanskrit" else "Gita GPT"
        return render_template('chat.html', 
                              chat_type=chat_type, 
                              chat_title=chat_title, 
                              chats=chats, 
                              current_chat=current_chat, 
                              messages=messages)
    except Exception as e:
        logger.error(f"Error loading chat page: {e}")
        flash('An error occurred while loading the chat page. Please try again.')
        return redirect(url_for('dashboard'))

@app.route('/create_chat', methods=['POST'])
def create_chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        chat_type = request.form.get('chat_type')
        if chat_type not in ['sanskrit', 'gita']:
            return jsonify({'success': False, 'error': 'Invalid chat type'}), 400
        
        user_id = session.get('user_id')
        
        new_chat = Chat(
            title="New Chat",
            chat_type=chat_type,
            user_id=user_id
        )
        db.session.add(new_chat)
        db.session.commit()
        
        redirect_url = url_for('chat_page', chat_type=chat_type, chat_id=new_chat.id)
        logger.info(f"Created new chat with ID {new_chat.id}, redirecting to {redirect_url}")
        
        return jsonify({
            'success': True, 
            'chat_id': new_chat.id,
            'redirect': redirect_url
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating chat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        user_id = session.get('user_id')
        chat_id = request.form.get('chat_id')
        message_content = request.form.get('message')
        
        # Validate chat belongs to user
        chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'success': False, 'error': 'Chat not found'}), 404
        
        # Save user message
        user_message = Message(
            content=message_content,
            is_user=True,
            chat_id=chat_id
        )
        db.session.add(user_message)
        
        # Update chat title if it's the first message
        if chat.title == "New Chat":
            # Use first few words of the message as the title
            title_preview = message_content[:30] + "..." if len(message_content) > 30 else message_content
            chat.title = title_preview
        
        # Get AI response
        try:
            client = get_ai_client()
            
            # Add context based on chat type
            system_message = ""
            if chat.chat_type == "sanskrit":
                system_message = """You are an expert in Sanskrit phrases and their meanings. Provide accurate translations and explanations of Sanskrit phrases, terms, and concepts only.
                
                If the user asks about topics unrelated to Sanskrit language, phrases, or culture, politely inform them that you can only provide information about Sanskrit phrases and related topics.
                
                Always maintain a respectful and educational tone when discussing Sanskrit language and culture."""
            else:  # gita
                system_message = """You are an expert on the Bhagavad Gita. Provide insights and explanations from the Gita's perspective only.

                If the user asks you regarding the author or version that you are using then inform them that you are using the version of the Gita that is authored by Sri Madhwacharya, a spiritual giant and philosopher.
                
                If the user asks about topics unrelated to the Bhagavad Gita, Hindu philosophy, or related spiritual concepts, politely inform them that you can only provide information related to the Bhagavad Gita and its teachings.
                
                Always maintain a respectful and spiritual tone when discussing the Gita's wisdom.
                
                If the user asks you about unrelated topics rather than Bhagavad Gita then inform them that Iam solely trained on Bhagavad Gita and not on other topics.
                
                Follow the strict rules of restricting yourself answering to topics other than Bhagavad Gita.
                
                If the user asks you about number of pages that you got trained on, inform them that you got trained on vast text of Bhagavad Gita and not on specific number of pages."""
            
            # Get chat history for context (last 10 messages)
            history = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.desc()).limit(10).all()
            history.reverse()  # Oldest first
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add chat history
            for msg in history:
                role = "user" if msg.is_user else "assistant"
                messages.append({"role": role, "content": msg.content})
            
            # Add current message if not already included
            if not history or history[-1].content != message_content:
                messages.append({"role": "user", "content": message_content})
            
            response = client.chat.completions.create(
                model="harshitha672/Phi_4_model_Finetuned_GitaGPT",
                messages=messages,
                temperature=0.7,
                max_tokens=10000
            )
            
            ai_response = response.choices[0].message.content
            
            # Save AI response
            ai_message = Message(
                content=ai_response,
                is_user=False,
                chat_id=chat_id
            )
            db.session.add(ai_message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'user_message': message_content,
                'ai_response': ai_response,
                'chat_title': chat.title
            })
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            # Fallback response
            ai_response = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
            # Save fallback response
            ai_message = Message(
                content=ai_response,
                is_user=False,
                chat_id=chat_id
            )
            db.session.add(ai_message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'user_message': message_content,
                'ai_response': ai_response,
                'chat_title': chat.title,
                'warning': 'Used fallback response due to AI service error'
            })
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_chat/<int:chat_id>', methods=['POST'])
def delete_chat(chat_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=session.get('user_id')).first()
        if not chat:
            return jsonify({'success': False, 'error': 'Chat not found'}), 404
        
        chat_type = chat.chat_type
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': url_for('chat_page', chat_type=chat_type)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting chat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rename_chat/<int:chat_id>', methods=['POST'])
def rename_chat(chat_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        new_title = request.form.get('title')
        if not new_title:
            return jsonify({'success': False, 'error': 'Title cannot be empty'}), 400
        
        chat = Chat.query.filter_by(id=chat_id, user_id=session.get('user_id')).first()
        if not chat:
            return jsonify({'success': False, 'error': 'Chat not found'}), 404
        
        chat.title = new_title
        db.session.commit()
        
        return jsonify({'success': True, 'title': new_title})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error renaming chat: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True)

