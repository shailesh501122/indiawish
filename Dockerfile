# Build stage
FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /app

# Copy solution and project files
COPY IndiaWish.sln .
COPY src/IndiaWish.Domain/IndiaWish.Domain/IndiaWish.Domain.csproj src/IndiaWish.Domain/IndiaWish.Domain/
COPY src/IndiaWish.Application/IndiaWish.Application/IndiaWish.Application.csproj src/IndiaWish.Application/IndiaWish.Application/
COPY src/IndiaWish.Infrastructure/IndiaWish.Infrastructure/IndiaWish.Infrastructure.csproj src/IndiaWish.Infrastructure/IndiaWish.Infrastructure/
COPY src/IndiaWish.Persistence/IndiaWish.Persistence/IndiaWish.Persistence.csproj src/IndiaWish.Persistence/IndiaWish.Persistence/
COPY src/IndiaWish.API/IndiaWish.API/IndiaWish.API.csproj src/IndiaWish.API/IndiaWish.API/

# Restore
RUN dotnet restore

# Copy everything and build
COPY . .
RUN dotnet publish src/IndiaWish.API/IndiaWish.API/IndiaWish.API.csproj -c Release -o /app/publish

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 80 443
ENTRYPOINT ["dotnet", "IndiaWish.API.dll"]
