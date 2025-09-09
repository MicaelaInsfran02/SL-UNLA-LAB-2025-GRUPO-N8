from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey
from datetime import date
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import relationship

# Crear motor de base de datos SQLite

# creo una base de datos llamada database.db
engine = create_engine('sqlite:///database.db', echo=True)
# Declarar la base
Base = declarative_base()
Session = sessionmaker(bind=engine)
# declaro las clases


class Persona(Base):
    __tablename__ = 'personas'
    # atributos de la tabla personas
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    edad = Column(Integer, nullable=False)
    dni = Column(Integer, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)
    # relacion con la tabla contacto
    contacto = relationship("Contacto", back_populates="persona", uselist=False)
    # relacion con la tabla turno
    turno = relationship("Turno", back_populates="persona", uselist=False)


class Turno(Base):
    __tablename__ = 'turnos'
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Integer, nullable=False)
    estado = Column(String, nullable=False)
    persona = Column(String, nullable=False)
    # relacion con la tabla persona (primero se crea la persona y despues el turno)
    persona_id = Column(Integer, ForeignKey('personas.id'))
    persona = relationship("Persona", back_populates="turno")


class Contacto(Base):
    __tablename__ = 'contactos'
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    telefono = Column(Integer, nullable=False)
    direccion = Column(String, nullable=False)
    localidad = Column(String, nullable=False)
    # relacion con la tabla persona (primero se crea la persona y despues el contacto)
    persona_id = Column(Integer, ForeignKey('personas.id'))
    persona = relationship("Persona", back_populates="contacto")


#if __name__ == "__main__":

    # Creo las tablas que declare mas arriba, solo si no existen
    Base.metadata.create_all(engine)
    # Crear una sesión para interactuar con la base
    Session = sessionmaker(bind=engine)
    session = Session()
    # Agregar una persona
    nueva_persona = Persona(
        nombre="Lucía Fernández",
        edad=22,
        dni=11111111,
        fecha_nacimiento= date(2004, 5, 30),
        habilitado=True
    )

    # Crear una instancia de Contacto asociada a la persona
    nuevo_contacto = Contacto(
        email="lucia.fernandez@example.com",
        telefono=112224444,
        direccion="Av. Siempreviva 123",
        localidad="CABA",
        persona=nueva_persona  # Establece la relación
    )

    # Agregar ambos objetos a la sesión
    session.add(nueva_persona)
    session.add(nuevo_contacto)

    #una vez que hago el commit subo los cambios a la base, siempre es un solo commit por archivo
    #(voy a tener un archivo por transsacion, ejemplo uno para eliminar, otro modificar, etc)
    session.commit()

    # Consultar personas
    #for persona in session.query(Persona).all():
    # print(persona.nombre, persona.edad)