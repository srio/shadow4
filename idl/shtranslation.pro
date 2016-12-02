FUNCTION shtranslation,a0,qdist1,file=file

; qdist: translation vector

IF N_ELEMENTS(qdist1) EQ 0 THEN qdist = [0D,0,0] ELSE qdist=qdist1 


a0=readsh(a0)
a=a0
ray=a.ray
ray[0,*]=ray[0,*]+qdist[0]
ray[1,*]=ray[1,*]+qdist[1]
ray[2,*]=ray[2,*]+qdist[2]

a.ray = ray
IF Keyword_Set(file) THEN putrays,a,file
RETURN,a
END


