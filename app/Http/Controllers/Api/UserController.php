<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\BulkStoreUsersRequest;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        // Definimos un límite seguro: por defecto 15, mínimo 1, máximo 100 por página
        $perPage = min(max((int) $request->input('per_page', 15), 1), 100);

        // Laravel extrae automáticamente el parámetro ?page= desde la URL
        $users = User::paginate($perPage);

        return response()->json($users);
    }

    public function emails(Request $request): JsonResponse
    {
        $perPage = min(max((int) $request->input('per_page', 15), 1), 100);

        // Seleccionamos únicamente los campos necesarios y aplicamos paginación
        $users = User::select('id', 'email')->paginate($perPage);

        return response()->json($users);
    }

    public function overTwenty(Request $request): JsonResponse
    {
        $cutoff = Carbon::now()->subYears(20)->startOfDay();
        $perPage = min(max((int) $request->input('per_page', 15), 1), 100);

        // CORRECCIÓN CLAVE: Filtramos directamente en la Base de Datos con where()
        $users = User::where('birth_date', '<=', $cutoff)->paginate($perPage);

        return response()->json($users);
    }

    public function bulkStore(BulkStoreUsersRequest $request): JsonResponse
    {
        $created = [];

        foreach ($request->validated()['users'] as $userData) {
            $created[] = User::create([
                'name' => $userData['name'],
                'email' => $userData['email'],
                'birth_date' => $userData['birth_date'],
                'password' => Hash::make($userData['password'] ?? 'password'),
            ]);
        }

        return response()->json([
            'message' => 'Se crearon los usuarios correctamente.',
            'users' => $created,
        ], 201);
    }
}