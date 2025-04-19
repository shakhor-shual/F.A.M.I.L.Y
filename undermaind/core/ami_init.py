cur.execute(
    "CALL public.init_ami_consciousness_level(%s, %s, %s, %s)",
    (
        self.ami_name,
        self.ami_password,
        self.ami_name,  # Возвращаем оригинальное имя схемы
        True
    )
) 