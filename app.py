# biblioteca para criar ids de string unicas
import uuid

# importa a biblioteca Flask
# jsonify: transforma objetos, como dicionários, em json
# request: captura a informação da requisição recebida pelas rotas
# make_response: usado para criar as respostas ao usuário
from flask import Flask, jsonify, request, make_response
# bibliota para facilitar a comunicac'ão com o DB
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

import jwt
import datetime

from functools import wraps

import joblib
import pandas as pd

DB_URL = 'postgresql://felipezeiser:s3nhas3nha@127.0.0.1:5432/API_ABEX'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SECRET_KEY'] = 'umachaveultrasecreta'

db = SQLAlchemy(app)

model = None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(512))

# mysql://username:password@host:port/database_name

def check_token(f):
    @wraps(f)

    def decorated(*args, **kwargs):
        # print(datetime.datetime.now())

        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token não encontrado.'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
            
            if not current_user:
                return({'message': 'Usuário inválido'}), 401
        except Exception as e:
            print(e)
            return jsonify({'message': 'Token não é válido.'}), 401

        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/user', methods=['POST'])
def create_user():

    data = request.get_json()

    if not data['password'] or not data['user']:
        return jsonify({'message':'Usuário ou senha não informados'}) 

    hashed_password = generate_password_hash(data['password'], method='pbkdf2')
    public_id = uuid.uuid4()

    new_user = User(public_id=public_id,
                    username=data['user'],
                    password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuário criado com sucesso.'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data['password'] or not data['user']:
        return jsonify({'message':'Usuário ou senha não informados'})
    
    user = User.query.filter_by(username=data['user']).first()

    if not user:
        return jsonify({'message':'Usuário inválido'})
    
    if check_password_hash(user.password, data['password']):
        token = jwt.encode({'public_id': user.public_id,
                            'exp': datetime.datetime.now() + datetime.timedelta(hours=24)},
                            app.config['SECRET_KEY'])
        return jsonify({'token': token}), 200
    
    return jsonify({'message': 'Erro ao gerar o token. Verifique as suas credenciais.'}), 401

@app.route('/predict', methods=['POST'])
@check_token
def predict(current_user):

    data = request.get_json()

    if not data:
        return jsonify({'message': 'Envie os dados para fazer a predicão'}), 500
    # print(data)

    try:
        X_test = {key: float(value) for key, value in data.items()}
        X_test = pd.DataFrame([X_test])
        prediction = model.predict(X_test)
        # print(prediction)

        return jsonify({'prediction': prediction.tolist()})
    except Exception as e:
        print(e)
        return jsonify({'message': 'Erro durante a predição. \
                        Consulte a documentação para verificar \
                         as chaves dos dados.'}), 500

if __name__ == '__main__':

    print("Carregando o modelo.....")
    model = joblib.load('rf_opt.joblib')
    print("Modelo carregado!")
    app.run(debug=True)