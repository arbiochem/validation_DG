// Toggle filters on mobile
document.getElementById('filterToggle').addEventListener('click', function() {
    const filtersSection = document.getElementById('filtersSection');
    const isHidden = filtersSection.style.maxHeight === '0px';
    
    if (isHidden) {
        filtersSection.style.maxHeight = '500px';
        filtersSection.style.padding = '1.5rem';
    } else {
        filtersSection.style.maxHeight = '0px';
        filtersSection.style.padding = '0';
    }
});

// Données pour les graphiques (à remplacer par des données Django)
const venteData = {
    labels: ['Site 1', 'Site 2', 'Site 3', 'Site 4', 'Site 5', 'Site 6'],
    values: [1350, 1180, 840, 630, 490, 260]
};

const achatData = {
    labels: ['Site 1', 'Site 2', 'Site 3', 'Site 4', 'Site 5', 'Site 6'],
    values: [1350, 1180, 840, 630, 490, 260]
};

const retardData = {
    labels: ['Client 1', 'Client 2', 'Client 3', 'Client 4', 'Client 5', 'Client 6'],
    values: [1350, 1180, 840, 630, 490, 260]
};

const pieVenteData = {
    labels: ['Segment 1', 'Segment 2', 'Segment 3', 'Segment 4'],
    values: [40, 20, 10, 30],
    colors: ['#9c27b0', '#4caf50', '#00bcd4', '#ff9800']
};

const pieAchatData = {
    labels: ['Segment 1', 'Segment 2', 'Segment 3', 'Segment 4'],
    values: [40, 20, 10, 30],
    colors: ['#9c27b0', '#4caf50', '#00bcd4', '#ff9800']
};

const grapheSitesData = {
    labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
    site1: [400, 300, 200, 278, 189, 239, 349, 200, 278, 189, 400, 300],
    site2: [240, 139, 980, 390, 480, 380, 430, 400, 210, 340, 280, 200],
    site3: [200, 221, 229, 200, 218, 250, 210, 180, 290, 240, 200, 350]
};

// Graphique Vente (Barres horizontales)
const venteCtx = document.getElementById('venteChart').getContext('2d');
new Chart(venteCtx, {
    type: 'bar',
    data: {
        labels: venteData.labels,
        datasets: [{
            label: 'Ventes',
            data: venteData.values,
            backgroundColor: '#4caf50',
            borderRadius: 4
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { 
                grid: { display: true, color: '#e0e0e0' }
            },
            y: {
                grid: { display: false }
            }
        }
    }
});

// Graphique Achat (Barres horizontales)
const achatCtx = document.getElementById('achatChart').getContext('2d');
new Chart(achatCtx, {
    type: 'bar',
    data: {
        labels: achatData.labels,
        datasets: [{
            label: 'Achats',
            data: achatData.values,
            backgroundColor: '#2196f3',
            borderRadius: 4
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { 
                grid: { display: true, color: '#e0e0e0' }
            },
            y: {
                grid: { display: false }
            }
        }
    }
});

// Graphique Retard (Barres horizontales)
const retardCtx = document.getElementById('retardChart').getContext('2d');
new Chart(retardCtx, {
    type: 'bar',
    data: {
        labels: retardData.labels,
        datasets: [{
            label: 'Retards',
            data: retardData.values,
            backgroundColor: '#9c27b0',
            borderRadius: 4
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { 
                grid: { display: true, color: '#e0e0e0' }
            },
            y: {
                grid: { display: false }
            }
        }
    }
});

// Graphique Pie Vente
const pieVenteCtx = document.getElementById('pieVenteChart').getContext('2d');
new Chart(pieVenteCtx, {
    type: 'pie',
    data: {
        labels: pieVenteData.labels,
        datasets: [{
            data: pieVenteData.values,
            backgroundColor: pieVenteData.colors,
            borderWidth: 2,
            borderColor: '#fff'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed + '%';
                    }
                }
            }
        }
    }
});

// Graphique Pie Achat
const pieAchatCtx = document.getElementById('pieAchatChart').getContext('2d');
new Chart(pieAchatCtx, {
    type: 'pie',
    data: {
        labels: pieAchatData.labels,
        datasets: [{
            data: pieAchatData.values,
            backgroundColor: pieAchatData.colors,
            borderWidth: 2,
            borderColor: '#fff'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed + '%';
                    }
                }
            }
        }
    }
});

// Graphique Sites (Barres groupées)
const grapheSitesCtx = document.getElementById('grapheSitesChart').getContext('2d');
new Chart(grapheSitesCtx, {
    type: 'bar',
    data: {
        labels: grapheSitesData.labels,
        datasets: [
            {
                label: 'Site 1',
                data: grapheSitesData.site1,
                backgroundColor: '#2196f3',
                borderRadius: 4
            },
            {
                label: 'Site 2',
                data: grapheSitesData.site2,
                backgroundColor: '#9c27b0',
                borderRadius: 4
            },
            {
                label: 'Site 3',
                data: grapheSitesData.site3,
                backgroundColor: '#e91e63',
                borderRadius: 4
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 12,
                    padding: 10
                }
            }
        },
        scales: {
            x: {
                grid: { display: false }
            },
            y: {
                grid: { display: true, color: '#e0e0e0' }
            }
        }
    }
});