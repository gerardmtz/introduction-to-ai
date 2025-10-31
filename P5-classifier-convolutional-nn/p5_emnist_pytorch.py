# ============================================================================
# CELDA 1: IMPORTS Y CONFIGURACIÓN INICIAL
# ============================================================================
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import torch
import torch.nn as nn
from tqdm.notebook import tqdm
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, TensorDataset
from sklearn.model_selection import train_test_split
import torchvision
import matplotlib.pyplot as plt
from IPython import display
import sklearn.metrics as skm
import copy

import matplotlib_inline
matplotlib_inline.backend_inline.set_matplotlib_formats("svg")

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Usando dispositivo: {device}")
print(f"PyTorch version: {torch.__version__}")

# ============================================================================
# SEMILLA DE REPRODUCIBILIDAD
# ============================================================================
def set_seed(seed=42):
    """Establece semilla para reproducibilidad"""
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Establecer semilla
set_seed(42)
print("Semilla de reproducibilidad establecida: 42")

# ============================================================================
# CELDA 2: IMPORTAR Y PREPARAR EL DATASET
# ============================================================================
print("Descargando dataset EMNIST...")
cdata = torchvision.datasets.EMNIST(root="emnist", split="letters", download=True)

print(f"All classes: {cdata.classes}")
print(f"Data size: {cdata.data.shape}")

# Transformando a tensor 4D para capas convolucionales
images = cdata.data.view([124800, 1, 28, 28]).float()
print(f"Tensor shape: {images.shape}")

# Eliminar clase 0 y ajustar etiquetas
letterCategories = cdata.classes[1:]
labels = copy.deepcopy(cdata.targets) - 1
print(f"Labels shape: {labels.shape}")
print(f"Número de muestras con label 0: {torch.sum(labels == 0)}")

# Normalizar imágenes
images /= torch.max(images)
print("Imágenes normalizadas al rango [0, 1]")

# ============================================================================
# CELDA 3: VISUALIZAR MUESTRAS DEL DATASET
# ============================================================================
fig, axes = plt.subplots(3, 7, figsize=(13, 6))

for i, ax in enumerate(axes.flatten()):
    which_pic = np.random.randint(images.shape[0])

    image = images[which_pic, 0, :, :].detach()
    letter = letterCategories[labels[which_pic]]

    ax.imshow(image.T, cmap='gray')
    ax.set_title(f"Letter: {letter}")
    ax.set_xticks([])
    ax.set_yticks([])
plt.suptitle("Muestras del Dataset EMNIST", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# ============================================================================
# CELDA 4: DIVISIÓN EN TRAIN/VALIDATION/TEST (75%/15%/15%)
# ============================================================================
print("\n" + "="*60)
print("DIVISIÓN DEL DATASET")
print("="*60)

# Primera división: 75% train, 25% temp (para val+test)
X_train, X_temp, y_train, y_temp = train_test_split(
    images, labels, test_size=0.25, random_state=42, stratify=labels
)

# Segunda división: 15% validation, 15% test (50% de temp cada uno)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

print(f"Train set: {X_train.shape[0]} muestras ({X_train.shape[0]/len(images)*100:.1f}%)")
print(f"Validation set: {X_val.shape[0]} muestras ({X_val.shape[0]/len(images)*100:.1f}%)")
print(f"Test set: {X_test.shape[0]} muestras ({X_test.shape[0]/len(images)*100:.1f}%)")

# Crear datasets y dataloaders
train_data = TensorDataset(X_train, y_train)
val_data = TensorDataset(X_val, y_val)
test_data = TensorDataset(X_test, y_test)

batch_size = 128
train_dl = DataLoader(train_data, batch_size=batch_size, shuffle=True, drop_last=True)
val_dl = DataLoader(val_data, batch_size=batch_size, shuffle=False)
test_dl = DataLoader(test_data, batch_size=batch_size, shuffle=False)

print(f"\nBatch size: {batch_size}")
print(f"Train batches: {len(train_dl)}")
print(f"Validation batches: {len(val_dl)}")
print(f"Test batches: {len(test_dl)}")

# ============================================================================
# CELDA 5: DEFINICIÓN DEL MODELO
# ============================================================================
def make_the_model(print_toggle):
    class EMNISTNet(nn.Module):
        def __init__(self, print_toggle):
            super().__init__()
            self.print_toggle = print_toggle

            # Conv1
            self.conv1 = nn.Conv2d(in_channels=1, out_channels=64, kernel_size=3, padding=1)
            self.bnorm1 = nn.BatchNorm2d(num_features=64)

            # Conv2
            self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3)
            self.bnorm2 = nn.BatchNorm2d(num_features=128)

            # Conv3
            self.conv3 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3)
            self.bnorm3 = nn.BatchNorm2d(num_features=256)

            self.fc1 = nn.Linear(in_features=2*2*256, out_features=256)
            self.fc2 = nn.Linear(in_features=256, out_features=64)
            self.fc3 = nn.Linear(in_features=64, out_features=26)

        def forward(self, x):
            if self.print_toggle:
                print(f"Input: {list(x.shape)}")

            # First Block: conv -> max_pool -> bnorm -> relu
            x = F.max_pool2d(self.conv1(x), 2)
            x = F.leaky_relu((self.bnorm1(x)))
            x = F.dropout(x, p=0.25, training=self.training)
            if self.print_toggle:
                print(f"First Block: {list(x.shape)}")

            # Second Block: conv -> max_pool -> bnorm -> relu
            x = F.max_pool2d(self.conv2(x), 2)
            x = F.leaky_relu((self.bnorm2(x)))
            x = F.dropout(x, p=0.25, training=self.training)
            if self.print_toggle:
                print(f"Second Block: {list(x.shape)}")

            # Third Block: conv -> max_pool -> bnorm -> relu
            x = F.max_pool2d(self.conv3(x), 2)
            x = F.leaky_relu((self.bnorm3(x)))
            x = F.dropout(x, p=0.25, training=self.training)
            if self.print_toggle:
                print(f"Third Block: {list(x.shape)}")

            # Reshape for linear layer
            n_units = x.shape.numel() / x.shape[0]
            x = x.view(-1, int(n_units))
            if self.print_toggle:
                print(f"Vectorized: {list(x.shape)}")

            # Linear layers
            x = F.leaky_relu(self.fc1(x))
            x = F.dropout(x, p=0.5, training=self.training)
            x = F.leaky_relu(self.fc2(x))
            x = F.dropout(x, p=0.5, training=self.training)
            x = self.fc3(x)
            if self.print_toggle:
                print(f"Final Output: {list(x.shape)}")

            return x

    model = EMNISTNet(print_toggle)
    loss_fun = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(params=model.parameters(), lr=0.001)

    return model, loss_fun, optimizer

# Test del modelo
print("\n" + "="*60)
print("ARQUITECTURA DEL MODELO")
print("="*60)
model, loss_fun, optimizer = make_the_model(True)
X, y = next(iter(train_dl))
y_hat = model(X)
loss = loss_fun(y_hat, torch.squeeze(y))
print(f"\nOutput: {y_hat.shape} | Loss inicial: {loss.item():.4f}")

# ============================================================================
# CELDA 6: CLASE EARLY STOPPING
# ============================================================================
class EarlyStopping:
    """Early stopping para detener el entrenamiento cuando la validación deja de mejorar."""

    def __init__(self, patience=5, min_delta=0.001, verbose=True):
        """
        Args:
            patience (int): Cuántas épocas esperar después de la última mejora
            min_delta (float): Cambio mínimo para considerar una mejora
            verbose (bool): Si True, imprime mensajes
        """
        self.patience = patience
        self.min_delta = min_delta
        self.verbose = verbose
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        self.best_model_state = None

    def __call__(self, val_loss, model):
        if self.best_loss is None:
            self.best_loss = val_loss
            self.save_checkpoint(model)
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.verbose:
                print(f'EarlyStopping counter: {self.counter} de {self.patience}')
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.save_checkpoint(model)
            self.counter = 0

    def save_checkpoint(self, model):
        """Guarda el estado del modelo cuando la validación mejora."""
        if self.verbose:
            print(f'Validation loss mejoró a {self.best_loss:.6f}. Guardando modelo...')
        self.best_model_state = copy.deepcopy(model.state_dict())

print("Clase EarlyStopping definida correctamente")

# ============================================================================
# CELDA 7: FUNCIÓN DE ENTRENAMIENTO CON FINE-TUNING
# ============================================================================
def train_the_model():
    """
    Entrena el modelo con:
    - Learning rate scheduler (ReduceLROnPlateau)
    - Early stopping
    - Validación en cada época
    """
    epochs = 30  # Máximo de épocas (early stopping puede detenerlo antes)
    model, loss_fun, optimizer = make_the_model(False)
    model = model.to(device)

    # Learning Rate Scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',           # Minimizar la loss de validación
        factor=0.5,           # Reducir LR a la mitad
        patience=3,           # Esperar 3 épocas sin mejora
        min_lr=1e-6
    )

    # Early Stopping
    early_stopping = EarlyStopping(patience=7, min_delta=0.001, verbose=True)

    # Métricas
    train_loss = []
    val_loss = []
    test_loss = []
    train_acc = []
    val_acc = []
    test_acc = []
    learning_rates = []

    print("\n" + "="*60)
    print("INICIANDO ENTRENAMIENTO")
    print("="*60)

    for epoch_i in range(epochs):
        print(f"\n{'='*60}")
        print(f"ÉPOCA {epoch_i+1}/{epochs}")
        print(f"{'='*60}")

        # ======================= ENTRENAMIENTO =======================
        model.train()
        batch_loss = []
        batch_acc = []

        for X, y in tqdm(train_dl, desc=f"Entrenando Época {epoch_i+1}"):
            X, y = X.to(device), y.to(device)

            y_hat = model(X)
            loss = loss_fun(y_hat, torch.squeeze(y))
            batch_loss.append(loss.item())

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            acc = torch.mean((torch.argmax(y_hat, axis=1) == y).float()).item()
            batch_acc.append(acc)

        epoch_train_loss = np.mean(batch_loss)
        epoch_train_acc = np.mean(batch_acc)
        train_loss.append(epoch_train_loss)
        train_acc.append(epoch_train_acc)

        # ======================= VALIDACIÓN =======================
        model.eval()
        val_batch_loss = []
        val_batch_acc = []

        with torch.no_grad():
            for X, y in tqdm(val_dl, desc=f"Validando Época {epoch_i+1}"):
                X, y = X.to(device), y.to(device)
                y_hat = model(X)
                loss = loss_fun(y_hat, torch.squeeze(y))
                val_batch_loss.append(loss.item())

                acc = torch.mean((torch.argmax(y_hat, axis=1) == y).float()).item()
                val_batch_acc.append(acc)

        epoch_val_loss = np.mean(val_batch_loss)
        epoch_val_acc = np.mean(val_batch_acc)
        val_loss.append(epoch_val_loss)
        val_acc.append(epoch_val_acc)

        # ======================= TEST =======================
        test_batch_loss = []
        test_batch_acc = []

        with torch.no_grad():
            for X, y in test_dl:
                X, y = X.to(device), y.to(device)
                y_hat = model(X)
                loss = loss_fun(y_hat, torch.squeeze(y))
                test_batch_loss.append(loss.item())

                acc = torch.mean((torch.argmax(y_hat, axis=1) == y).float()).item()
                test_batch_acc.append(acc)

        epoch_test_loss = np.mean(test_batch_loss)
        epoch_test_acc = np.mean(test_batch_acc)
        test_loss.append(epoch_test_loss)
        test_acc.append(epoch_test_acc)

        # Guardar learning rate actual
        current_lr = optimizer.param_groups[0]['lr']
        learning_rates.append(current_lr)

        # ======================= RESUMEN DE ÉPOCA =======================
        print(f"\nResultados Época {epoch_i+1}:")
        print(f"  Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc:.4f}")
        print(f"  Val Loss:   {epoch_val_loss:.4f} | Val Acc:   {epoch_val_acc:.4f}")
        print(f"  Test Loss:  {epoch_test_loss:.4f} | Test Acc:  {epoch_test_acc:.4f}")
        print(f"  Learning Rate: {current_lr:.6f}")

        # ======================= SCHEDULER =======================
        scheduler.step(epoch_val_loss)

        # ======================= EARLY STOPPING =======================
        early_stopping(epoch_val_loss, model)

        if early_stopping.early_stop:
            print(f"\n{'='*60}")
            print(f"EARLY STOPPING activado en época {epoch_i+1}")
            print(f"{'='*60}")
            # Restaurar el mejor modelo
            model.load_state_dict(early_stopping.best_model_state)
            break

    print(f"\n{'='*60}")
    print("ENTRENAMIENTO COMPLETADO")
    print(f"{'='*60}")

    return train_loss, val_loss, test_loss, train_acc, val_acc, test_acc, learning_rates, model

# ============================================================================
# CELDA 8: ENTRENAR EL MODELO
# ============================================================================
train_loss, val_loss, test_loss, train_acc, val_acc, test_acc, learning_rates, model = train_the_model()

print("\n¡Entrenamiento finalizado exitosamente!")

# ============================================================================
# CELDA 9: VISUALIZAR RESULTADOS DEL ENTRENAMIENTO
# ============================================================================
fig, ax = plt.subplots(2, 2, figsize=(14, 10))

# Loss
ax[0, 0].plot(train_loss, "s-", label="Train", linewidth=2)
ax[0, 0].plot(val_loss, "o-", label="Validation", linewidth=2)
ax[0, 0].plot(test_loss, "^-", label="Test", linewidth=2)
ax[0, 0].set_xlabel("Épocas", fontsize=12)
ax[0, 0].set_ylabel("Loss (CrossEntropy)", fontsize=12)
ax[0, 0].set_title("Pérdida del Modelo", fontsize=14, fontweight='bold')
ax[0, 0].legend(fontsize=10)
ax[0, 0].grid(True, alpha=0.3)

# Accuracy
ax[0, 1].plot(train_acc, "s-", label="Train", linewidth=2)
ax[0, 1].plot(val_acc, "o-", label="Validation", linewidth=2)
ax[0, 1].plot(test_acc, "^-", label="Test", linewidth=2)
ax[0, 1].set_xlabel("Épocas", fontsize=12)
ax[0, 1].set_ylabel("Accuracy", fontsize=12)
ax[0, 1].set_title(f"Precisión del Modelo\nTest Final: {test_acc[-1]:.4f}",
                   fontsize=14, fontweight='bold')
ax[0, 1].legend(fontsize=10)
ax[0, 1].grid(True, alpha=0.3)

# Learning Rate
ax[1, 0].plot(learning_rates, "d-", color='purple', linewidth=2)
ax[1, 0].set_xlabel("Épocas", fontsize=12)
ax[1, 0].set_ylabel("Learning Rate", fontsize=12)
ax[1, 0].set_title("Learning Rate Schedule", fontsize=14, fontweight='bold')
ax[1, 0].set_yscale('log')
ax[1, 0].grid(True, alpha=0.3)

# Resumen de métricas finales
final_metrics = f"""
MÉTRICAS FINALES

Train Accuracy:      {train_acc[-1]:.4f}
Validation Accuracy: {val_acc[-1]:.4f}
Test Accuracy:       {test_acc[-1]:.4f}

Train Loss:          {train_loss[-1]:.4f}
Validation Loss:     {val_loss[-1]:.4f}
Test Loss:           {test_loss[-1]:.4f}

Épocas entrenadas:   {len(train_loss)}
"""

ax[1, 1].text(0.1, 0.5, final_metrics, fontsize=12, verticalalignment='center',
              fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax[1, 1].axis('off')

plt.tight_layout()
plt.show()

# ============================================================================
# CELDA 10: VISUALIZAR PREDICCIONES
# ============================================================================
# Obtener todas las predicciones del test set
model.eval()
all_preds = []
all_labels = []
all_images = []

with torch.no_grad():
    for X, y in test_dl:
        X, y = X.to(device), y.to(device)
        y_hat = model(X)
        preds = torch.argmax(y_hat, axis=1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(y.cpu().numpy())
        all_images.extend(X.cpu().numpy())

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)
all_images = np.array(all_images)

# Visualizar predicciones
rand_idx = np.random.choice(len(all_labels), size=21, replace=False)

fig, axs = plt.subplots(3, 7, figsize=(14, 7))

for i, ax in enumerate(axs.flatten()):
    idx = rand_idx[i]
    image = np.squeeze(all_images[idx, 0, :, :])
    true_letter = letterCategories[all_labels[idx]]
    pred_letter = letterCategories[all_preds[idx]]

    cmap = "gray" if true_letter == pred_letter else "hot"

    ax.imshow(image.T, cmap=cmap)
    ax.set_title(f"True: {true_letter} | Pred: {pred_letter}", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])

plt.suptitle("Predicciones del Modelo (Gris=Correcto, Rojo=Error)",
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# ============================================================================
# CELDA 11: MATRIZ DE CONFUSIÓN
# ============================================================================
C = skm.confusion_matrix(all_labels, all_preds, normalize='true')

fig = plt.figure(figsize=(10, 10))
plt.imshow(C, "Blues", vmax=0.5)

plt.xticks(range(26), labels=letterCategories, fontsize=10)
plt.yticks(range(26), labels=letterCategories, fontsize=10)
plt.xlabel("Predicción", fontsize=12, fontweight='bold')
plt.ylabel("Etiqueta Real", fontsize=12, fontweight='bold')
plt.title("Matriz de Confusión (Test Set)", fontsize=14, fontweight='bold')
plt.colorbar(label='Proporción')

# Agregar valores en las celdas
for i in range(26):
    for j in range(26):
        text_color = 'white' if C[i, j] > 0.25 else 'black'
        plt.text(j, i, f'{C[i, j]:.2f}', ha='center', va='center',
                color=text_color, fontsize=6)

plt.tight_layout()
plt.show()

# ============================================================================
# CELDA 12: ANÁLISIS DETALLADO POR LETRA
# ============================================================================
# Calcular métricas por clase
from sklearn.metrics import classification_report

print("\n" + "="*60)
print("REPORTE DE CLASIFICACIÓN")
print("="*60)
print(classification_report(all_labels, all_preds, target_names=letterCategories, digits=4))

# Encontrar las letras con mejor y peor rendimiento
accuracies_per_letter = np.diag(C)
sorted_indices = np.argsort(accuracies_per_letter)

print("\n" + "="*60)
print("ANÁLISIS POR LETRA")
print("="*60)
print("\n5 LETRAS CON MEJOR ACCURACY:")
for idx in sorted_indices[-5:][::-1]:
    print(f"  {letterCategories[idx]}: {accuracies_per_letter[idx]:.4f}")

print("\n5 LETRAS CON PEOR ACCURACY:")
for idx in sorted_indices[:5]:
    print(f"  {letterCategories[idx]}: {accuracies_per_letter[idx]:.4f}")

print("\n" + "="*60)
print("FIN DEL ANÁLISIS")
print("="*60)