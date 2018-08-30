SELECT codePostal, category.name, price
FROM lbc2.objects
	INNER JOIN category ON objects.idCategory = category.idCategory
	INNER JOIN localisation ON objects.idLoc = localisation.idLoc
WHERE price IS NOT NULL
ORDER BY price DESC;
