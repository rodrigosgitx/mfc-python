datos = {'alto' : 1200}

contorno = {
    "01" : 1200,
    "02" : 1600,
    "99" : 9999,
    }

for a in contorno:
        if datos['alto'] <= contorno[a]:
            altura = a
            break
        
print (altura)