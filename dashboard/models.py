from django.db import models

class FComptet(models.Model):
    ct_num = models.CharField(primary_key=True, max_length=20)
    ct_intitule = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'F_COMPTET'

class FDocentete(models.Model):
    do_piece = models.CharField(max_length=50)
    do_ref = models.CharField(max_length=50, blank=True, null=True)
    do_tiers = models.ForeignKey(FComptet, models.DO_NOTHING, db_column='DO_Tiers')
    do_statut = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'F_DOCENTETE'

class FDOCLIGNE(models.Model):
    do_piece = models.CharField(max_length=50)
    cbMarq = models.AutoField(primary_key=True)
    AR_Ref = models.CharField(max_length=100)
    DL_DESIGN = models.CharField(max_length=255)
    DL_QTE = models.DecimalField(max_digits=10, decimal_places=2)
    DL_PrixUnitaire = models.DecimalField(max_digits=10, decimal_places=2)
    DL_Frais = models.DecimalField(max_digits=10, decimal_places=2)
    DL_MontantHT = models.DecimalField(max_digits=10, decimal_places=2)
    DL_MontantTTC = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'F_DOCLIGNE'

