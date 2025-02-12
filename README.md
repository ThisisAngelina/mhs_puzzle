# My Healthy Skin Diagnostic

## 🏥 About the Project
**My Healthy Skin Diagnostic** is a Django-based web application that provides users with insights into their lifestyle habits and their potential impact on skin health. The app features a quiz that evaluates various aspects of a user's lifestyle, calculates category scores, builds graphs based on results, and generates personalized recommendations using AI integration.

## 🚀 Features
- **Interactive Quiz:** Users complete a questionnaire assessing different lifestyle categories (e.g., sleep, stress, nutrition).
- **AI-Powered Recommendations:** Utilizes OpenAI's ChatGPT to generate actionable lifestyle advice based on quiz results.
- **Data Visualization:** Uses Matplotlib to generate graphical representations of category scores.
- **Session Management:** Leverages Django sessions to track user progress through the quiz.
- **Performance Optimization:** Implements Redis for caching and in-memory data retrieval.
- **Custom User Experience:** Bootstrap-based responsive UI for an enhanced user experience.
- **Automated CI/CD:** Configured GitHub Actions for automated testing and deployment.
- **Security & Privacy:** Users remain anonymous, with only usernames and category results being stored.

## 🛠 Technologies Used
### **Backend**
- Python (Django Framework)
- OpenAI API (ChatGPT)
- Redis (for caching quiz data and recommendations)
- Django Sessions
- Matplotlib (for generating graphs)

### **Frontend**
- HTML, CSS, JavaScript
- Bootstrap (for UI styling)
- Django Templating Engine

### **DevOps & Deployment**
- GitHub Actions (CI/CD pipeline for automated testing and deployment)
- Docker (Optional for containerized deployment)
- Whitenoise, Gunicorn & Nginx (for production server setup)

## 🔧 Installation & Setup
### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/ThisisAngelina/mhs_puzzle.git
```

### **2️⃣ Set Up a Virtual Environment**
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3️⃣ Install Dependencies**
```sh
pip install -r requirements.txt
```

### **4️⃣ Configure Environment Variables**
Create a `.env` file and set the required credentials:
```env
OPENAI_API_KEY=your-api-key
REDIS_URL=redis://127.0.0.1:6379/1
DEBUG=True
SECRET_KEY=your-secret-key
```

### **5️⃣ Apply Migrations & Run Server**
```sh
cd mhs_puzzle_prj
python manage.py migrate
python manage.py runserver
```

### **6️⃣ Start Redis Server (For Caching)**
```sh
redis-server
```

## 📊 Usage
1. **Start the quiz** and answer questions related to lifestyle habits.
2. **View your results** in graphical format with personalized insights.
3. **Get AI-powered recommendations** based on your scores.
4. **Improve your lifestyle** with actionable steps!

## 🛡 Security & Privacy
- Users remain **anonymous**—only usernames and quiz results are stored.
- No personal data (e.g., email, name) is collected.
- Session management ensures **secure user interactions**.

## ✅ CI/CD with GitHub Actions
The project uses **GitHub Actions** for continuous integration and deployment:
- **Automated Testing:** Runs Django unit tests before merging.
- **Static Code Analysis:** Ensures code quality with linters.
- **Deployment Automation:** Auto-deploys updates to the production server.

## 📌 Contributing
Contributions are welcomed! To contribute:
1. **Fork the repository**
2. **Create a new branch** (`feature-new-feature`)
3. **Commit your changes**
4. **Push to your fork**
5. **Create a pull request**

## 📩 Contact
For questions or feedback, reach out via email:
📧 **angelina.chigrinetc.dev@gmail.com**

