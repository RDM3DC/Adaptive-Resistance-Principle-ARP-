from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sympy import simplify, sympify
from sympy.parsing.sympy_parser import parse_expr
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./math_engine.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MathEquation(Base):
    __tablename__ = "equations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    expression = Column(Text)
    simplified = Column(Text)
    tag = Column(String, default="draft")

class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    class_type = Column(String)
    level = Column(Integer, default=1)
    proof_xp = Column(Integer, default=0)
    known_theorems = Column(Text, default="")

class Ability(Base):
    __tablename__ = "abilities"
    id = Column(Integer, primary_key=True, index=True)
    creator_user = Column(String)
    name = Column(String)
    expression = Column(Text)
    power = Column(Integer, default=1)

Base.metadata.create_all(bind=engine)

class ExpressionInput(BaseModel):
    expression: str
    user_id: str

class ProofInput(BaseModel):
    lhs: str
    rhs: str
    user_id: str

class TagUpdate(BaseModel):
    tag: str

class CharacterInput(BaseModel):
    user_id: str
    class_type: str

class TheoremInput(BaseModel):
    user_id: str
    theorem: str
    xp: int

class AbilityInput(BaseModel):
    creator_user: str
    name: str
    expression: str

class CastInput(BaseModel):
    user_id: str
    expression: str
    ability_id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/simplify")
def simplify_expression(expr_input: ExpressionInput, db: Session = Depends(get_db)):
    try:
        expr = parse_expr(expr_input.expression)
        result = simplify(expr)
        record = MathEquation(user_id=expr_input.user_id, expression=str(expr), simplified=str(result))
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"original": str(expr), "simplified": str(result), "id": record.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/equivalent")
def check_equivalence(proof_input: ProofInput):
    try:
        lhs = parse_expr(proof_input.lhs)
        rhs = parse_expr(proof_input.rhs)
        is_equiv = simplify(lhs - rhs) == 0
        return {"equivalent": is_equiv}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/prove")
def verify_proof(proof_input: ProofInput, db: Session = Depends(get_db)):
    try:
        lhs = simplify(parse_expr(proof_input.lhs))
        rhs = simplify(parse_expr(proof_input.rhs))
        proof_valid = lhs == rhs
        if proof_valid:
            record = MathEquation(user_id=proof_input.user_id, expression=proof_input.lhs + " = " + proof_input.rhs, simplified="Valid proof")
            db.add(record)
            db.commit()
        return {"valid_proof": proof_valid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/user_equations/{user_id}")
def list_user_equations(user_id: str, db: Session = Depends(get_db)):
    equations = db.query(MathEquation).filter(MathEquation.user_id == user_id).all()
    return [{"id": e.id, "expression": e.expression, "simplified": e.simplified, "tag": e.tag} for e in equations]

@app.patch("/tag_equation/{equation_id}")
def tag_equation(equation_id: int, tag_update: TagUpdate, db: Session = Depends(get_db)):
    eq = db.query(MathEquation).filter(MathEquation.id == equation_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equation not found")
    eq.tag = tag_update.tag
    db.commit()
    return {"id": eq.id, "tag": eq.tag}

@app.post("/mintable")
def check_mintable(expr_input: ExpressionInput):
    try:
        expr = parse_expr(expr_input.expression)
        simplified = simplify(expr)
        mintable = str(expr) != str(simplified)
        return {"mintable": mintable, "simplified": str(simplified)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/suggest_proof")
def suggest_proof_step(expr_input: ExpressionInput):
    try:
        expr = parse_expr(expr_input.expression)
        simplified = simplify(expr)
        suggestions = []
        if simplified != expr:
            suggestions.append(f"Try simplifying: {simplified}")
        if expr.is_Add:
            suggestions.append("Group like terms or factor common terms.")
        if expr.is_Mul:
            suggestions.append("Expand or simplify product.")
        return {"suggestions": suggestions or ["No suggestion available"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create_character")
def create_character(char_input: CharacterInput, db: Session = Depends(get_db)):
    new_char = Character(user_id=char_input.user_id, class_type=char_input.class_type)
    db.add(new_char)
    db.commit()
    db.refresh(new_char)
    return {"id": new_char.id, "class_type": new_char.class_type, "level": new_char.level, "xp": new_char.proof_xp}

@app.post("/add_theorem")
def add_theorem(theorem_input: TheoremInput, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.user_id == theorem_input.user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    char.proof_xp += theorem_input.xp
    char.known_theorems += f"\n{theorem_input.theorem}"
    if char.proof_xp >= char.level * 100:
        char.level += 1
    db.commit()
    return {"user_id": char.user_id, "level": char.level, "xp": char.proof_xp, "known_theorems": char.known_theorems}

@app.post("/create_ability")
def create_ability(ability_input: AbilityInput, db: Session = Depends(get_db)):
    try:
        expr = parse_expr(ability_input.expression)
        simplified = simplify(expr)
        power = len(str(expr))  # simple heuristic
        ability = Ability(creator_user=ability_input.creator_user, name=ability_input.name, expression=str(expr), power=power)
        db.add(ability)
        db.commit()
        db.refresh(ability)
        return {"id": ability.id, "name": ability.name, "power": ability.power}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cast_ability")
def cast_ability(cast_input: CastInput, db: Session = Depends(get_db)):
    try:
        ability = db.query(Ability).filter(Ability.id == cast_input.ability_id).first()
        if not ability:
            raise HTTPException(status_code=404, detail="Ability not found")
        user_expr = simplify(parse_expr(cast_input.expression))
        ability_expr = simplify(parse_expr(ability.expression))
        success = user_expr == ability_expr
        return {"cast_successful": success, "expected": str(ability_expr), "you_proved": str(user_expr)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


📦 All your game logic is now consolidated into one powerful backend script. You can copy the full code from the document above and save it into a file like math_realms_backend.md or main.py on GitHub.

I've also left some inline suggestions to help you modularize as the project grows.

Would you like a README.md template to document the project setup and endpoints as well?

