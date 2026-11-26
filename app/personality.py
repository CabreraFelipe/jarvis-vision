"""Fixed, validated response preferences. No user-authored system instructions."""
OPTIONS=(
    ('Formalidad',('Predeterminada','Formal','Informal')),
    ('Humor',('Predeterminado','Sin humor','Sutil')),
    ('Extensión',('Predeterminada','Breve','Amplia')),
    ('Tratamiento',('Predeterminado','Vos','Tú','Usted')),
    ('Iniciativa',('Predeterminada','Solo responder','Sugerir próximos pasos')),
)
DEFAULT=tuple(values[0] for _,values in OPTIONS)

def validate(values):
    if not isinstance(values,(list,tuple)) or len(values)!=len(OPTIONS):
        raise ValueError('Perfil de personalidad inválido.')
    if any(value not in allowed for value,(_,allowed) in zip(values,OPTIONS)):
        raise ValueError('Opción de personalidad inválida.')
    return tuple(values)

INSTRUCTIONS=(
    {'Formal':'Usá un registro formal.','Informal':'Usá un registro informal.'},
    {'Sin humor':'Evitá las bromas.','Sutil':'Usá humor sutil solo cuando sea apropiado.'},
    {'Breve':'Priorizá respuestas breves.','Amplia':'Ampliá detalles relevantes.'},
    {'Vos':'Dirigite al usuario de vos.','Tú':'Dirígete al usuario de tú.','Usted':'Dirígete al usuario de usted.'},
    {'Solo responder':'No agregues sugerencias no solicitadas salvo aclaraciones necesarias.','Sugerir próximos pasos':'Cuando ayude, sugerí próximos pasos sin afirmar que los ejecutaste.'},
)
def instruction(values):
    values=validate(values)
    return ' '.join(mapping[value] for value,mapping in zip(values,INSTRUCTIONS) if value in mapping)
